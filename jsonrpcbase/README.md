# jsonrpcbase

Simple JSON-RPC service without transport layer.

This repository includes a vendored copy of [jsonrpcbase](https://pypi.org/project/kbase-jsonrpcbase/) version `0.3.0a6` to resolve dependency conflicts.

Note that there exists a [github repo](https://github.com/kbaseincubator/jsonrpcbase) which is presumably the source of the PyPi module, but it appears to only contain the alpha5 release of the code vs. PyPi's alpha6. It is not clear where the alpha6 code resides other than PyPi.

The original repository was only used by this project, so the code has been brought in directly to simplify maintenance and eliminate external dependency issues.