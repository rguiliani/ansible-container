# -*- coding: utf-8 -*-

from __future__ import absolute_import
from collections import OrderedDict


import logging

logger = logging.getLogger(__name__)


class Service(object):

    def __init__(self, config=None, project_name=None):
        self.project_name = project_name
        self.config = config

    def get_template(self):
        return self._get_task_or_config(request_type="config")

    def get_task(self):
        return self._get_task_or_config(request_type="task")

    def _get_task_or_config(self, request_type="task"):
        templates = []
        for name, service in self.config.get('services', {}).items():
            new_service = self._create(request_type, name, service)
            if new_service:
                templates.append(new_service)
        return templates

    def _create(self, type, name, service):
        '''
        Generate an Openshift service configuration or playbook task.
        '''
        template = {}
        ports = self._get_ports(service)
        options = service.get('options', {}).get('openshift', {})
        state = options.get('state', 'present')

        if ports:
            labels = dict(
                app=self.project_name,
                service=name
            )
            if type == 'config' and state != 'absent':
                template = dict(
                    apiVersion="v1",
                    kind="Service",
                    metadata=dict(
                        name=name,
                        labels=labels.copy()
                    ),
                    spec=dict(
                        selector=labels.copy(),
                        ports=ports,
                    )
                )
            elif type == 'task':
                template = dict(
                    oso_service=OrderedDict(
                        project_name=self.project_name,
                        service_name=name,
                        labels=labels.copy(),
                        ports=ports,
                        selector=labels.copy()
                    )
                )
                if state != 'present':
                    template['oso_service']['state'] = state

        return template

    def _get_ports(self, service):
        # TODO - handle port ranges
        ports = []
        for port in service.get('ports', []):
            if isinstance(port, str) and ':' in port:
                parts = port.split(':')
                if not self._port_in_list(parts[0], ports):
                    ports.append(dict(port=int(parts[0]), targetPort=int(parts[1]), name='port-%s' % parts[0]))
            else:
                if not self._port_in_list(port, ports):
                    ports.append(dict(port=int(port), targetPort=int(port), name='port-%s' % port))

        for port in service.get('expose', []):
            if not self._port_in_list(port, ports):
                ports.append(dict(port=int(port), targetPort=int(port), name='port-%s' % port))
        return ports

    @staticmethod
    def _port_in_list(port, ports):
        found = False
        for p in ports:
            if p['port'] == int(port):
                found = True
                break
        return found

