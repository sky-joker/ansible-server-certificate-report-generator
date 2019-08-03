FROM quay.io/ansible/default-test-container:latest
RUN cd /opt && \
    git clone https://github.com/ansible/ansible.git && \
    cd ansible && \
    mkdir lib/ansible/modules/salf_made/ && \
    mkdir test/units/modules/salf_made && \
    touch lib/ansible/modules/salf_made/__init__.py
ADD tests/ansible_module_test.sh /opt
ADD library/* /opt/ansible/lib/ansible/modules/salf_made/
RUN chmod +x /opt/ansible_module_test.sh
RUN apt-get -y install man-db