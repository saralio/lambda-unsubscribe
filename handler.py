import boto3
from saral_utils.extractor.dynamo import DynamoDB
from saral_utils.utils.env import get_env_var


def remove_user_frm_db(event, context):

    email_id = event['queryStringParameters']['emailId']
    print(f'Unsubscribing for emailid: {email_id}')
    suggestion = event['queryStringParameters'].get('suggestion')
    suggestion = 'No suggestion' if suggestion is None else suggestion

    region = get_env_var('MY_REGION')
    env = get_env_var('MY_ENV')
    table = f'deregistered-users-{env}'

    db = DynamoDB(table=table, env=env, region=region)
    db.put_item(
        payload={'emailId': {'S': email_id}, 'isActive': {'BOOL': False}}
    )
    print('Updated dynamodb successfully')

    # updating event bridge rule
    rule_client = boto3.client('events')
    rule_name = f'RuleFor_{email_id.replace("@", "_").replace(".", "_")}'
    response = rule_client.disable_rule(Name=rule_name)
    print(f'Disabled the event bridge rule successfully. Response returned: {response}')


    # trigger an email to info@saral.club
    ses_client = boto3.client('ses')
    body = f'User [{email_id}] unsubscribed and gave following suggestion: {suggestion}'

    try:
        response = ses_client.send_email(
            Destination={'ToAddresses': ['info@saral.club']},
            Message={
                'Body': {'Text': {'Data': body}},
                'Subject': {'Data': 'A user unsubscribed'}
            },
            Source="support@saral.club"
        )
    except Exception as error: 
        print(f'Unable to send email. Error returned: {error}')


    return {
        'statusCode': 200,
        'headers': {
            "Content-Type": "text/html",
            "Access-Control-Allow_Headers": "Content-Type",
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'Get'
        }
    }
