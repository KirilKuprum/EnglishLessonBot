import datetime

import boto3

from botocore.exceptions import ClientError

class DataBase:
    def __init__(self, table_name, region):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=region)
        self.table = self.dynamodb.Table(table_name)

    def __str__(self):
        return str(self.table)

    def put_item(self, item: dict):
        item['created_at'] = str(datetime.datetime.now())
        self.table.put_item(
            Item=item
        )
    def get_item(self, user_id: int) -> dict | None:
        try:
            response = self.table.get_item(
                Key={'user_id': str(user_id)} 
            )
            return response.get('Item')
        except ClientError as e:
            print(f"Помилка отримання даних з DynamoDB: {e.response['Error']['Message']}")
            return None
        
    def update_index(self, user_id, index):
        self.table.update_item(
            Key={'user_id': str(user_id)},
            UpdateExpression="SET current_index = :val",
            ExpressionAttributeValues={':val': index}
        )
