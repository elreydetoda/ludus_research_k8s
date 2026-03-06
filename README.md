# Kubernetes Ludus Setup

Infrastructure automation for deploying reproducible Kubernetes security labs using [Bad Sector Labs'](https://docs.ludus.cloud) infrastructure automation tool, Ludus.

This repository provisions Kubernetes clusters and optional telemetry and vulnerability components for attack simulation, detection engineering, and runtime security research.

## Pre-requisites

- Ubuntu 24.04 template added to Ludus

## Installation

```bash
git clone https://github.com/heilancoos/ludus_k8s
ludus range config set -f ludus_k8s/config.yml
ludus ansible role add -d ./roles/install_k8s
ludus ansible role add -d ./roles/telemetry
```

## Usage

### `install_k8s` Role

| Variable           | Type    | Options / Notes                                                                 |
| ------------------ | ------- | ------------------------------------------------------------------------------- |
| `k8s_flavor`       | string  | `microk8s`                                                                      |
| `microk8s_addons`  | list    | See [MicroK8s Addons](https://canonical.com/microk8s/docs/addons)               |
| `microk8s_user`    | string  | User to configure kubectl access for                                            |
| `multinode`        | boolean | Enable multi-node cluster setup                                                 |
| `control_node`     | boolean | Mark this node as the control plane (required when `multinode: true`)           |
| `worker_only`      | boolean | Join as worker-only node (set when `multinode: true`)                           |
| `node`             | boolean | Join as full node (set when `multinode: true`)                                  |

### `telemetry` Role

| Variable             | Type    | Options / Notes                                               |
| -------------------- | ------- | ------------------------------------------------------------- |
| `telemetry_stack`    | string  | `falco`                                                       |
| `telemetry_role`     | string  | `agent` deploys Falco on cluster<br>`ui` — deploys Falcosidekick UI<br>`full` deploys both |
| `telemetry_hostname` | string  | Hostname/IP of the node running the telemetry UI             |
| `ui`                 | string  | `grafana`  deploys Loki + Grafana instead of Falcosidekick UI |

### Vulnerability Modules

These are optional misconfigurations that can be enabled to create realistic attack surfaces for research and training.

| Variable               | Type    | Description                                                                 |
| ---------------------- | ------- | --------------------------------------------------------------------------- |
| `enable_unauth_api`    | boolean | Enables anonymous auth on the Kubernetes API server and Kubelet             |
| `enable_exposed_etcd`  | boolean | Exposes etcd without authentication                                         |

## Example Config

```yaml
ludus:
  - vm_name: "{{ range_id }}-k8s-control"
    hostname: "k8s-control"
    template: ubuntu-24-x64-server-template
    vlan: 10
    ip_last_octet: 1
    ram_gb: 8
    cpus: 4
    linux: true
    roles:
      - name: install_k8s
        vars:
          k8s_flavor: microk8s
          microk8s_user: ubuntu
          microk8s_addons:
            - dns
            - helm3
          multinode: false
      - name: telemetry
        vars:
          telemetry_stack: falco
          telemetry_role: full
          telemetry_hostname: "{{ range_id }}-k8s-control"
          ui: grafana
          enable_unauth_api: true
          enable_exposed_etcd: false
```