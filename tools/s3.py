import boto3
import logging

s3 = boto3.resource('s3')
bucket_name = 'git-lit'
bucket = s3.Bucket(bucket_name)

def get(filename): 
    object = s3.Object(bucket_name,filename)

def list(): 
    for obj in bucket.objects.all():
        print(obj.key)
