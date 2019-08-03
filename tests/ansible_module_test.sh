#!/bin/sh
version=$1
module_dir='lib/ansible/modules/salf_made/'

cd /opt/ansible
. hacking/env-setup
for module in $(find $module_dir | grep "\.py$" | awk -F / '{print $(NF)}' | sed -e "s/\.py$//g" | grep -v "__init__" | sort) ; do
    if [ $version = "2.6" ] ; then
        ansible-test sanity --python $version --skip-test botmeta $module
    elif [ $version = "3.8" ] ; then
        ansible-test sanity --python $version --skip-test pylint $module
    else
        ansible-test sanity --python $version $module
    fi

    if [ $? -ne 0 ] ; then
      exit 1
    fi
done