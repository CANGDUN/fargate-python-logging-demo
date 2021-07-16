import logging
import subprocess
import os
import urllib.request as req
import json

import boto3

def print_log():
    '''書式設定を行い ERROR, WARNING, INFO の各段階でログを出力する'''

    logging.basicConfig(format='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s', datefmt='(%z) %Y/%m/%d %H:%M:%S',level=logging.INFO)
    logging.error('Something is going wrong...')
    logging.warning('Watch out!')
    logging.info('Hello from Fargate!')
    logging.info('こんにちは Fargate!')

def subprocess_aws_api():
    '''subprocess より AWS CLI を実行する'''

    subprocess.run(['aws', '--version'])
    subprocess.run(['aws', 'ec2', 'describe-instances', '--query', 'Reservations[].Instances[].InstanceId'])

def boto3_aws_api():
    '''boto3 より AWS API を発行する'''

    logging.info(f'boto3 version: {boto3.__version__}')
    EC2 = boto3.client('ec2')
    instances_dict = EC2.describe_instances()
    logging.info([instance['InstanceId'] for reservation in instances_dict['Reservations'] for instance in reservation['Instances']])

def print_ecs_task_info():
    '''ECS タスクメタデータを取得しタスクの ARN とログストリームを出力する'''

    ecs_metadata = json.loads(req.urlopen(os.getenv('ECS_CONTAINER_METADATA_URI_V4')).read())
    logging.info(f'ECS Task ARN: {ecs_metadata["Labels"]["com.amazonaws.ecs.task-arn"]}')
    logging.info(f'Log Stream: {ecs_metadata["LogOptions"]["awslogs-stream"]}')

if __name__ == '__main__':
    print_log()
    print_ecs_task_info()
    subprocess_aws_api()
    boto3_aws_api()
