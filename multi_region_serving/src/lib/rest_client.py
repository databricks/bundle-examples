import urllib.request
import json
from databricks.sdk.runtime import spark
 
class RestClient:
    def __init__(self, context):
        self.base_url = "https://" + spark.conf.get("spark.databricks.workspaceUrl")
        self.token = context.apiToken().get()

    def get_share_info(self, share_name:str):
        return self._get(f'api/2.1/unity-catalog/shares/{share_name}?include_shared_data=true')
    
    def _get(self, uri):
        url = f'{self.base_url}/{uri}'
        headers = { 'Authorization': f'Bearer {self.token}'}
        req = urllib.request.Request(url, headers=headers)
        try:
            response = urllib.request.urlopen(req)
            return json.load(response)
        except urllib.error.HTTPError as e:
            result = e.read().decode()
            print((e.code, result))