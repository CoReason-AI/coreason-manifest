import sys

from pydantic import ValidationError

from coreason_manifest.adapters.mcp.schemas import OMOPDomain, OMOPResourceTemplate


def test_malicious_uri(uri: str) -> None:
    try:
        OMOPResourceTemplate(uri_template=uri, resource_type=OMOPDomain.CONCEPT, description="Test malformed URI.")
        print(f"Error: Malicious URI '{uri}' was incorrectly accepted!")
        sys.exit(1)
    except ValidationError:
        # Expected
        pass


def main() -> None:
    malicious_uris = [
        "http://malicious.com",
        "omop:/missing-slash",
        "ftp://omop.com",
        "omop://valid/but/then?query=malicious",
    ]

    for uri in malicious_uris:
        test_malicious_uri(uri)

    print("LLM fuzzing sanity check passed. All malicious URIs rejected.")
    sys.exit(0)


if __name__ == "__main__":
    main()
