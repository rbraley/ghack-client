#!/bin/bash

protoc --proto_path=protocol --python_out=src/proto/ protocol/protocol.proto
