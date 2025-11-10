import yaml

def load_metadata(path="metadata.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_policies(path="policy.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    metadata = load_metadata()
    policies = load_policies()
    print("✅ Metadata Columns:", [c["name"] for c in metadata["columns"]])
    print("✅ Policy Rules:", [p["rule"] for p in policies["policies"]])
