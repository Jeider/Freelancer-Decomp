# Third-party build inputs

The private host is generated from DLSS5-Feeder v0.7.0:
https://github.com/jlrouzies-fr/DLSS5-Feeder/tree/v0.7.0

Its MIT license, Copyright (c) 2026 Jean-Laurent ROUZIES, including attribution
to NIGos, is copied by `tools/base_neural/prepare.py` into the runtime package.
`build_host.py` applies explicit checked modifications to that pinned source;
the generated source is in `out/base_neural/on/obj/host`.

The adapter uses the ReShade add-on SDK bundled with that pinned release
(Copyright Patrick Mours, SPDX BSD-3-Clause OR MIT). ReShade runtime binaries
and the RenoDX add-on are copied from the user's existing local installation.

NVIDIA NGX headers and link library are downloaded from a pinned NVIDIA/DLSS
revision and verified against Git blob hashes. The accompanying NVIDIA license
is included in the staged package. DLSS and DLSSNR runtime binaries are copied
from the user's existing installation. No NVIDIA binary is committed here.

dgVoodoo 2.87.6 is fetched from the author's GitHub release with a pinned SHA256.
Third-party downloads, models and executables remain under `out/base_neural`.
