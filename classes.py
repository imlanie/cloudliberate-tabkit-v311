#from dropbox.exceptions import AuthError
#import dropbox
import boto3
import logging


class S3BucketManager:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3')

    def create_bucket(self):
        response = self.s3_client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': 'us-west-2'
            }
        )
        return response

    def list_objects(self, prefix=None):
        if prefix is None:
            response = self.s3_client.list_objects(Bucket=self.bucket_name)
        else:
            response = self.s3_client.list_objects(
                Bucket=self.bucket_name, Prefix=prefix)

        print(response)
        return response

    def upload_file(self, file_path, object_name=None):
        if object_name is None:
            object_name = file_path

        response = self.s3_client.upload_file(
            file_path, self.bucket_name, object_name)
        return response

    def download_file(self, object_name, file_path):
        response = self.s3_client.download_file(
            self.bucket_name, object_name, file_path)
        return response

    def delete_object(self, object_name):
        response = self.s3_client.delete_object(
            Bucket=self.bucket_name, Key=object_name)
        return response

    def delete_bucket(self):
        response = self.s3_client.delete_bucket(Bucket=self.bucket_name)
        return response

    def list_objects_in_folder(self, folder_path):
        folder_path = folder_path.strip('/')
        prefix = folder_path + '/'
        objects = self.list_objects(prefix=prefix)
        return objects


class StringManager:
    def __init__(self, string):
        self.string = string

    def get_length(self):
        """Returns the length of the string."""
        return len(self.string)

    def reverse(self):
        """Returns the reverse of the string."""
        return self.string[::-1]

    def count_substring(self, substring):
        """Returns the number of occurrences of a substring in the string."""
        return self.string.count(substring)

    def get_substring(self, start_index, end_index):
        """Returns the substring between the specified start and end indices."""
        return self.string[start_index:end_index]

    def replace_substring(self, old_substring, new_substring):
        """Replaces all occurrences of a substring with a new substring."""
        return self.string.replace(old_substring, new_substring)


class Logger:
    def __init__(self, filename):
        self.filename = filename
        self.logger = logging.getLogger('my_logger')
        self.logger.setLevel(logging.DEBUG)

        # Create a file handler and set its level to DEBUG
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(logging.DEBUG)

        # Create a formatter and set it to the handler
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Add the handler to the logger
        self.logger.addHandler(file_handler)

    def log(self, message, level=logging.INFO):
        if level == logging.INFO:
            self.logger.info(message)
        elif level == logging.WARNING:
            self.logger.warning(message)
        elif level == logging.ERROR:
            self.logger.error(message)
        elif level == logging.CRITICAL:
            self.logger.critical(message)
        else:
            self.logger.debug(message)


class DropboxFileManager:
    def __init__(self, access_token):
        self.access_token = access_token
        self.client = dropbox.Dropbox(self.access_token)

    def upload_file(self, local_file_path, dropbox_file_path):
        try:
            with open(local_file_path, 'rb') as file:
                self.client.files_upload(file.read(), dropbox_file_path)
            print("File uploaded successfully!")
        except AuthError as e:
            print("Authentication failed. Please check your access token.")
        except Exception as e:
            print(f"An error occurred while uploading the file: {e}")

    def download_file(self, dropbox_file_path, local_file_path):
        try:
            with open(local_file_path, 'wb') as file:
                metadata, response = self.client.files_download(
                    dropbox_file_path)
                file.write(response.content)
            print("File downloaded successfully!")
        except AuthError as e:
            print("Authentication failed. Please check your access token.")
        except Exception as e:
            print(f"An error occurred while downloading the file: {e}")

    def delete_file(self, dropbox_file_path):
        try:
            self.client.files_delete_v2(dropbox_file_path)
            print("File deleted successfully!")
        except AuthError as e:
            print("Authentication failed. Please check your access token.")
        except Exception as e:
            print(f"An error occurred while deleting the file: {e}")

    def create_folder(self, dropbox_folder_path):
        try:
            self.client.files_create_folder_v2(dropbox_folder_path)
            print("Folder created successfully!")
        except AuthError as e:
            print("Authentication failed. Please check your access token.")
        except Exception as e:
            print(f"An error occurred while creating the folder: {e}")

    def move_file(self, source_file_path, destination_file_path):
        try:
            self.client.files_move_v2(source_file_path, destination_file_path)
            print("File moved successfully!")
        except AuthError as e:
            print("Authentication failed. Please check your access token.")
        except Exception as e:
            print(f"An error occurred while moving the file: {e}")

    def copy_file(self, source_file_path, destination_file_path):
        try:
            self.client.files_copy_v2(source_file_path, destination_file_path)
            print("File copied successfully!")
        except AuthError as e:
            print("Authentication failed. Please check your access token.")
        except Exception as e:
            print(f"An error occurred while copying the file: {e}")

    def get_metadata(self, dropbox_path):
        try:
            metadata = self.client.files_get_metadata(dropbox_path)
            print("Metadata retrieved successfully!")
            return metadata
        except AuthError as e:
            print("Authentication failed. Please check your access token.")
        except Exception as e:
            print(f"An error occurred while retrieving metadata: {e}")

    def search_files(self, dropbox_folder_path, query):
        try:
            results = self.client.files_search(dropbox_folder_path, query)
            print("Search results retrieved successfully!")
            return results
        except AuthError as e:
            print("Authentication failed. Please check your access token.")
        except Exception as e:
            print(f"An error occurred while searching for files: {e}")
