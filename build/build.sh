#!/bin/sh

FILENAME=`tlosint-$(date + "%Y-%m-%d")`
BASEDIR=$(dirname "$0")

cd $BASEDIR

packer build --force packer.json

pushd ./output
    qemu-img convert -f qcow2 tlosint.qcow2 -O vmdk ${FILENAME}.vmdk
    python ./scripts/generate_ovf.py ${FILENAME}
    sha1sum *.ovf *.vmdk | awk 'BEGIN { FIELDWIDTHS = "40 2 1024" } { print "SHA1(" $3 ")= " $1 }' > ${FILENAME}.mf
    tar -cvf ${FILENAME}.ova ${FILENAME}.vmdk ${FILENAME}.ovf ${FILENAME}.mf
    sha256sum ${FILENAME}.ova > ${FILENAME}.sha256sum
popd

pip3 install awscli

mkdir ~/.aws
cat << EOF > ~/.aws/config
[default]
region = ca-central-1
s3 =
  max_concurrent_requests = 100
  max_queue_size = 1000
  multipart_threshold = 50MB
  multipart_chunksize = 10MB
EOF

cat << EOF > ~/.aws/credentials
[default]
aws_access_key_id=$AWS_ACCESS_KEY
aws_secret_access_key=$AWS_SECRET_KEY
EOF

for f in ${FILENAME}.ova ${FILENAME}.sha256sum; do
    aws s3 rm s3://${BUCKET}/tlosint/nightly/${f}
    aws s3 cp ${f} s3://${BUCKET}/tlosint/nightly/
    aws s3api put-object-acl --bucket ${BUCKET} --key tlosint/nightly/${f} --acl public-read
done