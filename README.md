# fargate-python-logging-demo

- AWS Fargate における Python スクリプトのログ出力の検証

## How to use

- CloudFormation スタックのデプロイ
- `--parameters` オプションで各パラメーターの値を設定する

    ```sh
    aws cloudformation create-stack \
    --stack-name python-logging-ecr \
    --template-body file://ecr-repository.yml \
    --parameters ParameterKey=ECRRepositoryName,ParameterValue=python-logging

    aws cloudformation create-stack \
    --stack-name python-logging-ecs \
    --template-body file://ecs-cluster-taskdef-taskrole.yml \
    --parameters ParameterKey=ContainerImageTag,ParameterValue=python-logging:latest
    --capabilities CAPABILITY_NAMED_IAM
    ```

- ECR にログインする

    ```sh
    aws ecr get-login-password | docker login --username AWS --password-stdin {AWS_ACCOUNT_ID}.dkr.ecr.{region}.amazonaws.com
    ```

- ECR 用コンテナイメージの build と push

    ```sh
    docker build -t {AWS_ACCOUNT_ID}.dkr.ecr.{region}.amazonaws.com/python-logging:latest .
    docker push {AWS_ACCOUNT_ID}.dkr.ecr.{region}.amazonaws.com/python-logging:latest
    ```

- ECS タスク定義の更新

    ```sh
    aws ecs register-task-definition \
    --family python-logging-task-def \
    --task-role-arn arn:aws:iam::{AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole \
    --execution-role-arn arn:aws:iam::{AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole \
    --network-mode awsvpc \
    --requires-compatibilities FARGATE \
    --cpu 256 \
    --memory 512 \
    --container-definitions '[{\"name\": \"python\",\"image\": \"{AWS_ACCOUNT_ID}.dkr.ecr.{region}.amazonaws.com/python-logging:latest\",\"cpu\": 0,\"essential\": true,\"logConfiguration\": {\"logDriver\": \"awslogs\",\"options\": {\"awslogs-group\": \"/ecs/python-logging-task-def\",\"awslogs-region\": \"{region}\",\"awslogs-stream-prefix\": \"ecs\"}}}]'
    ```

- VPC 内でタスクを実行

    ```sh
    aws ecs run-task \
    --cluster ecs-logging-test \
    --count 1 \
    --enable-execute-command \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxxxxxxxxxxxxx],securityGroups=[sg-xxxxxxxxxxxxxxxxx],assignPublicIp=ENABLED}" \
    --task-definition python-logging-task-def:1
    ```

- CloudFormation スタックの削除

    ```sh
    aws cloudformation delete-stack --stack-name python-logging-ecr
    aws cloudformation delete-stack --stack-name python-logging-ecs
    ```

## 実行結果

- AWS CLI で CloudWatch Logs ログイベントを確認する

    ```sh
    aws logs get-log-events \
    --log-group-name /ecs/python-logging-task-def \
    --log-stream-name ecs/python/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
    --query events[].message
    ```

- ログイベントの内容(`aws logs` コマンド実行結果)

    ```log
    [
        "[(+0000) 2021/07/16 00:00:00.084] [ERROR] Something is going wrong...",
        "[(+0000) 2021/07/16 00:00:00.084] [WARNING] Watch out!",
        "[(+0000) 2021/07/16 00:00:00.085] [INFO] Hello from Fargate!",
        "[(+0000) 2021/07/16 00:00:00.085] [INFO] こんにちは Fargate!",
        "[(+0000) 2021/07/16 00:00:00.092] [INFO] ECS Task ARN: arn:aws:ecs:{region}:{AWS_ACCOUNT_ID}:task/ecs-logging-test/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "[(+0000) 2021/07/16 00:00:00.092] [INFO] Log Stream: ecs/python/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "aws-cli/1.20.0 Python/3.9.6 Linux/4.14.225-168.357.amzn2.x86_64 exec-env/AWS_ECS_FARGATE botocore/1.21.0",
        "[",
        "    \"i-xxxxxxxxxxxxxxxxx\",",
        "    \"i-xxxxxxxxxxxxxxxxx\",",
        "    \"i-xxxxxxxxxxxxxxxxx\"",
        "]",
        "[(+0000) 2021/07/16 00:00:05.396] [INFO] boto3 version: 1.18.0",
        "[(+0000) 2021/07/16 00:00:05.877] [INFO] ['i-xxxxxxxxxxxxxxxxx', 'i-xxxxxxxxxxxxxxxxx', 'i-xxxxxxxxxxxxxxxxx']"
    ]
    ```

## ECS Exec

- ECS Exec により実行中のコンテナに対してコマンド実行ができる
  - ホストに Session Manager プラグインのインストールが必要

___

- タスク実行時、`--overrides` オプションでタスク定義の設定を上書きする
- `command` に `sleep infinity` を指定し眠り続けた状態にする

    ```sh
    aws ecs run-task \
    --cluster ecs-logging-test \
    --count 1 \
    --enable-execute-command \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxxxxxxxxxxxxx],securityGroups=[sg-xxxxxxxxxxxxxxxxx],assignPublicIp=ENABLED}" \
    --task-definition python-logging-task-def:1
    --overrides '{\"containerOverrides\": [{\"name\": \"python\", \"command\": [\"sleep\", \"infinity\"]}]}'
    ```

- コンテナに対してコマンドを実行

    ```sh
    aws ecs execute-command \
    --cluster ecs-logging-test \
    --task xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
    --container python \
    --interactive \
    --command "/bin/sh"
    ```

- タスク実行時に `--enable-execute-command` オプションをつけ忘れた場合に ECS Exec を有効にする
- 使用可能になるのは次に起動するタスクからとなるため、`--force-new-deployment` オプションで強制的にタスクを作り直す

    ```sh
    aws ecs update-service \
    --cluster ecs-logging-test \
    --service python \
    --enable-execute-command \
    --force-new-deployment
    ```
