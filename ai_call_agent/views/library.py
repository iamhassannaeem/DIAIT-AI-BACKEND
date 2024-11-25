import os

import boto3
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai_call_agent.models import File
from ai_call_agent.serializers import FileSerializer


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        file_type = request.query_params.get("file_type", None)
        queryset = File.objects.filter(user=request.user)

        if file_type:
            queryset = queryset.filter(file_type=file_type)
        queryset = queryset.order_by("created_date")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        file_obj = self.request.FILES.get("file")
        if not file_obj:
            return Response(
                {"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )
        if file_obj.size > 100 * 1024 * 1024:
            return Response(
                {"error": "File size exceeds 100 MB limit."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        file_extension = os.path.splitext(file_obj.name)[1].lower()
        if file_extension not in [".txt", ".pdf"]:
            return Response(
                {"error": "Please upload a valid file format (txt or pdf)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        bucket_name = settings.AWS_S3_BUCKET_NAME
        file_instance = serializer.save(user=self.request.user)
        user_folder = f"{self.request.user.id}/"
        pk_folder = f"{file_instance.pk}/"
        folder_path = user_folder + pk_folder
        full_file_name = folder_path + file_obj.name

        response = s3.put_object(
            Bucket=bucket_name,
            Key=full_file_name,
            Body=file_obj,
            ContentType=file_obj.content_type,
        )

        request_id = response["ResponseMetadata"]["RequestId"]
        file_size_bytes = file_obj.size
        metadata = {
            "file_size_bytes": file_size_bytes,
            "file_size_kb": file_size_bytes / 1024,
            "file_size_mb": file_size_bytes / (1024**2),
            "file_size_gb": file_size_bytes / (1024**3),
            "content_type": file_obj.content_type,
            "last_modified": timezone.now(),
        }

        file_instance.file_name = file_obj.name
        file_instance.file_type = file_extension
        file_instance.request_id = request_id
        file_instance.file_size = metadata["file_size_bytes"]
        file_instance.content_type = metadata["content_type"]
        file_instance.last_modified = metadata["last_modified"]
        file_instance.s3_key = full_file_name
        file_instance.save()

        return Response(
            {
                "status": "File uploaded successfully.",
                "file_size_bytes": f"{metadata['file_size_bytes']} bytes",
                "file_size_kb": f"{metadata['file_size_kb']:.2f} KB",
                "file_size_mb": f"{metadata['file_size_mb']:.2f} MB",
                "file_size_gb": f"{metadata['file_size_gb']:.2f} GB",
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["put"])
    def replace_file(self, request, pk=None):
        file_instance = self.get_object()
        file_obj = request.FILES.get("file")

        if not file_obj:
            return Response(
                {"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

        if file_obj.size > 100 * 1024 * 1024:
            return Response(
                {"error": "File size exceeds 100 MB limit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_extension = os.path.splitext(file_obj.name)[1].lower()
        if file_extension not in [".txt", ".pdf"]:
            return Response(
                {"error": "Please upload a valid file format (txt or pdf)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        bucket_name = settings.AWS_S3_BUCKET_NAME
        if file_instance.s3_key:
            s3.delete_object(Bucket=bucket_name, Key=file_instance.s3_key)

        user_folder = f"{self.request.user.id}/"
        pk_folder = f"{file_instance.pk}/"
        folder_path = user_folder + pk_folder
        full_file_name = folder_path + file_obj.name

        response = s3.put_object(
            Bucket=bucket_name,
            Key=full_file_name,
            Body=file_obj,
            ContentType=file_obj.content_type,
        )

        request_id = response["ResponseMetadata"]["RequestId"]
        file_size_bytes = file_obj.size
        metadata = {
            "file_size_bytes": file_size_bytes,
            "file_size_kb": file_size_bytes / 1024,
            "file_size_mb": file_size_bytes / (1024**2),
            "file_size_gb": file_size_bytes / (1024**3),
            "content_type": file_obj.content_type,
            "last_modified": timezone.now(),
        }

        file_instance.file_name = file_obj.name
        file_instance.file_type = file_extension
        file_instance.request_id = request_id
        file_instance.file_size = metadata["file_size_bytes"]
        file_instance.content_type = metadata["content_type"]
        file_instance.last_modified = metadata["last_modified"]
        file_instance.s3_key = full_file_name
        file_instance.save()

        return Response(
            {
                "status": "File replaced successfully.",
                "file_size_bytes": f"{metadata['file_size_bytes']} bytes",
                "file_size_kb": f"{metadata['file_size_kb']:.2f} KB",
                "file_size_mb": f"{metadata['file_size_mb']:.2f} MB",
                "file_size_gb": f"{metadata['file_size_gb']:.2f} GB",
            },
            status=status.HTTP_200_OK,
        )

    def download(self, request, file_name):
        bucket_name = settings.AWS_S3_BUCKET_NAME
        user_id_folder = f"{self.request.user.id}/"
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=user_id_folder)
        files_in_folder = [obj["Key"] for obj in response.get("Contents", [])]
        matching_file = next(
            (file for file in files_in_folder if file.endswith(file_name)), None
        )

        if not matching_file:
            return Response(
                {"error": "File not found."}, status=status.HTTP_404_NOT_FOUND
            )

        s3_response = s3.get_object(Bucket=bucket_name, Key=matching_file)
        file_content = s3_response["Body"].read()
        content_type = s3_response["ContentType"]
        if content_type.startswith("text/"):
            response = HttpResponse(
                file_content.decode("utf-8"), content_type=content_type
            )
        else:
            response = HttpResponse(
                file_content, content_type="application/octet-stream"
            )

        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        bucket_name = settings.AWS_S3_BUCKET_NAME
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        user_id = request.user.id
        file_name_in_s3 = f"{user_id}/{instance.pk}/{instance.file_name}"

        s3.delete_object(Bucket=bucket_name, Key=file_name_in_s3)
        self.perform_destroy(instance)

        return Response(
            {"status": "File deleted successfully."}, status=status.HTTP_204_NO_CONTENT
        )
