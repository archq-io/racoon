# 🦝 Racoon

🦝 Racoon is a Python 3 tool for retrieving multiple files sequentally, as
specified in a manifest file. This is useful in data pipelines, CI/CD and generally
anywhere you need to gather multiple different files from various sources.

It can also:
 - copy local files
 - check the downloaded file checksum
 - check the downloaded zip file contents

# Installation
You can install Racoon using pip:
```
pip install git+https://github.com/archq-io/racoon
```

# Usage
Run the `racoon manifest.yaml` command or load a manifest directly from an URL
by running the `racoon https://raw.githubusercontent.com/.../master/manifest.yaml`
command.

**Note:** `rget` is an alias of the `racoon` command.

# Racoon Manifest v1 file format specification
```yaml
before:
  files: [] # Same as "files" below, but guaranteed to run first
files:
  - url: file:///home/user/file.bin
    destination: file-copy.bin
  - url: https://raw.githubusercontent.com/.../master/img/file.png
    destination: file.png
  - url: https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-12.5.0-amd64-netinst.iso
    destination: debian-12.5.0-amd64-netinst.iso
    verify:
      digest:
        algorithm: sha256
        text: f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2 # Specify a checksum
        file: # or load a checksum from a file
          url: https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/SHA256SUMS # Multiple checksums not supported yet
  - url: https://example.com/gtfs/gtfs.zip
    destination: gtfs.zip
    verify:
      archive:
        contains:
          - agency.txt
          - calendar_dates.txt
          - fare_attributes.txt
          - routes.txt
          - stops.txt
          - stop_times.txt
          - trips.txt
after:
  files: [] # Same as "files" above, but guaranteed to run last
includes:
  - url: file:///home/user/manifest.yaml
  - url: https://raw.githubusercontent.com/.../master/manifest.yaml
```
**Note:** This file format specification can change at any time and should not
be considered stable.

# Contribution
You can contribute to this project by opening an issue or a PR.
For other inquiries you can send an email to
<a href="mailto:info@archq.io">info@archq.io</a>.

# Project license
All files of this project are licensed under the
<a href="https://spdx.org/licenses/GPL-2.0-only.html">GNU General Public License v2.0 only</a>,  
unless noted otherwise.

🦝 Racoon  
Copyright (C) 2024 Luka Kovačič  

This program is free software; you can redistribute it and/or modify it under  
the terms of the GNU General Public License as published by the Free Software  
Foundation; version 2 of the License is the only valid version as far as this  
project is concerned and is not compatible with the GPL v3 or any other future  
version of the GNU General Public License.  

This program is distributed in the hope that it will be useful, but  
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or  
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more  
details.  

You should have received a copy of the GNU General Public License along with  
this program; there should be a COPYING file in the project root.  
