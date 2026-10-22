import argparse
import json


parser = argparse.ArgumentParser()
parser.add_argument("--warehouse-id", default="")
parser.add_argument("--cluster-policy-id", default="")
parser.add_argument("--service-principal-id", default="")
parser.add_argument("--cluster-id", default="")
parser.add_argument("--job-id", default="")
parser.add_argument("--metastore-id", default="")
args = parser.parse_args()

resolved = {
    "warehouse_id": args.warehouse_id,
    "cluster_policy_id": args.cluster_policy_id,
    "service_principal_id": args.service_principal_id,
    "cluster_id": args.cluster_id,
    "job_id": args.job_id,
    "metastore_id": args.metastore_id,
}
print("resolved_lookups=" + json.dumps(resolved, sort_keys=True))
