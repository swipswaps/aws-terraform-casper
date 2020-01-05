from states.terraform import TerraformState

import re
import boto3
import json
import tempfile


class AWSState(TerraformState):

    def __init__(
        self,
        profile=None,
        bucket=None,
        load_state=False
    ):
        self._resource_group_remap = {
            'aws_spot_instance_request': 'aws_instance'
        }
        self.session = boto3.Session()
        self.state_object = "terraform_state"

        if profile:
            self.session = boto3.Session(profile_name=profile)

        super().__init__(profile=profile, bucket=bucket, load_state=load_state)

    def _save_state(self):
        s3_client = self.session.client('s3')
        with tempfile.NamedTemporaryFile(mode='w+') as fid:
            fid.write(json.dumps(self.state_resources))
            fid.flush()
            s3_client.upload_file(
                fid.name, self.bucket, self.state_object
            )

    def _load_state(self):
        s3 = self.session.resource('s3')
        obj = s3.Object(self.bucket, self.state_object)
        data = obj.get()['Body'].read()

        self.state_resources = json.loads(data)

    @classmethod
    def _get_field(cls, field, resource):
        pattern = f"(?<={field})(.*?)(?=\\n)"
        return re.search(pattern, resource)[0].lstrip(' =')

    def _get_state_aws_instance(self, text):
        return self._get_field('id', text)

    def _get_state_aws_autoscaling_group(self, text):
        return self._get_field('id', text)

    def _get_state_aws_spot_instance_request(self, text):
        return self._get_field('spot_instance_id', text)

    def _get_state_aws_security_group(self, text):
        return self._get_field('id', text)

    def _get_state_aws_s3_bucket(self, text):
        return self._get_field('id', text)