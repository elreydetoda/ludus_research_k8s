# Kubernetes Ludus Setup

Infrastructure automation for deploying reproducible Kubernetes security labs using [Bad Sector Labs'](https://docs.ludus.cloud) infrastructure automation tool, Ludus.

This repository provisions Kubernetes clusters (MicroK8s or kubeadm) with optional telemetry and vulnerability components for attack simulation, detection engineering, and runtime security research.

## Pre-requisites

- Ubuntu 24.04 template added to Ludus

## Installation

```bash
git clone https://github.com/heilancoos/ludus_k8s
ludus range config set -f ludus_k8s/config.yml
ludus ansible role add -d ./roles/install_k8s
ludus ansible role add -d ./roles/telemetry
```

---

## `install_k8s` Role

### Core Variables

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `k8s_flavor` | string | `microk8s` (default) or `kubeadm` |
| `k8s_user` | string | Unprivileged user that owns the kubeconfig (default: `localuser`) |

### MicroK8s Variables

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `microk8s_addons` | list | Addons to enable (default: `dns`, `storage`, `helm3`). See [MicroK8s Addons](https://canonical.com/microk8s/docs/addons) |
| `microk8s_version` | string | Snap channel to pin (e.g. `"1.31/stable"`). Empty string installs latest stable |
| `multinode` | boolean | Enable multi-node cluster setup |
| `control_node` | boolean | Mark this node as the control plane (required when `multinode: true`) |
| `worker_only` | boolean | Join as worker-only node (set when `multinode: true`) |
| `node` | boolean | Join as full node (set when `multinode: true`) |

### kubeadm Variables

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `kubeadm_version` | string | Kubernetes minor version stream to install (e.g. `"1.31"`) |
| `k8s_cni` | string | CNI plugin: `calico` (default, 192.168.0.0/16) or `cilium` (10.0.0.0/8) |

---

## `telemetry` Role

### Core Variables

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `ui` | string | `grafana` — deploys Loki + Grafana<br>`falcosidekick` — deploys Falcosidekick with built-in web UI<br>omit for Falco only |
| `falco_custom_rules` | list | Rule names (exact strings) to apply from the bundled `rules.yaml`. Default: `[]`. All macros and lists are always included for dependency resolution |

### Falco Variables

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `falco_namespace` | string | Namespace for Falco and related components (default: `falco`) |
| `falco_chart_version` | string | Helm chart version to pin (default: latest) |
| `falco_nodeport` | integer | NodePort for the k8saudit webhook service (default: `30007`) |
| `falcosidekick_nodeport` | integer | NodePort for Falcosidekick; `0` = ClusterIP only (default: `0`) |
| `falcosidekick_webui_nodeport` | integer | NodePort for the Falcosidekick web UI when `ui: falcosidekick` (default: `30088`) |

### Grafana Variables

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `grafana_namespace` | string | Namespace for Grafana and Loki (default: `grafana`) |
| `grafana_nodeport` | integer | NodePort for Grafana web UI (default: `30147`) |

### Available Falco Rules

Rules live in `roles/telemetry/tasks/deps/rules.yaml`. Reference rules by exact name in `falco_custom_rules`:

| Category | Rule Name |
| -------- | --------- |
| Anonymous API | `Anonymous Request Allowed` |
| Anonymous API | `Anonymous Request Failed` |
| Anonymous API | `Anonymous Resource Access` |
| Anonymous API | `Anonymous Pod Creation Attempt` |
| Kubelet API | `Kubelet Remote Exec Attempt` |
| Kubelet API | `Anonymous Kubelet API Enumeration` |
| CoreDNS | `CoreDNS Rewrite Rule Added` |
| CoreDNS | `CoreDNS ConfigMap Modified` |
| CoreDNS | `Unusual CoreDNS Access Attempt` |
| etcd | `ETCD Access` |
| etcd | `ETCD Pod Tampering` |
| etcd | `ETCD read attempt from unusual source detected` |
| etcd | `ETCD Snapshot Created` |
| etcd | `ETCD Registry Deletion` |
| Golden Ticket | `Read of Kubernetes CA Key` |
| Golden Ticket | `Suspicious ServiceAccount Enumeration` |
| Golden Ticket | `Kubernetes Private Key Exfil` |
| RBAC | `ClusterRole Binding To Anonymous User` |
| RBAC | `ClusterRole Binding To Cluster Admin` |
| RBAC | `RBAC Wildcard Permissions Detected` |
| RBAC | `Namespaced SA Bound to ClusterRole` |
| ServiceAccount | `CLI Token Usage by Local Process` |
| ServiceAccount | `Pod ServiceAccount Token File Access` |
| ServiceAccount | `Privileged or Host-Level Container Creation` |
| Writable Mounts | `Symlink To Host Files` |
| Writable Mounts | `Pod Using hostPath to Mount Root Filesystem` |
| Writable Mounts | `Container Accessing Mounted Host Root Filesystem` |
| Admission Controller | `Modify Admission Webhook Configuration` |
| Admission Controller | `Read Admission Webhook Configurations` |
| Admission Controller | `Delete Admission Webhook Configuration` |

---

## Vulnerability Modules

Optional misconfigurations that create realistic attack surfaces for research and training.

### Unauthenticated API Server

Enables anonymous authentication on the Kubernetes API server. Requests reach the API as `system:anonymous`.

| Variable | Type | Description |
| -------- | ---- | ----------- |
| `enable_unauth_api` | boolean | Enable `--anonymous-auth=true` on the API server |

> Pair with `anon_cluster_admin: true` to also grant `system:anonymous` full cluster-admin access via RBAC.

### Unauthenticated Kubelet API

Enables anonymous authentication and sets authorization mode to `AlwaysAllow` on the kubelet. Exposes the kubelet exec endpoint at port 10250 without credentials. Installs `kubeletctl`.

| Variable | Type | Description |
| -------- | ---- | ----------- |
| `enable_unauth_kubelet` | boolean | Enable anonymous auth + `AlwaysAllow` on the kubelet |

### Unauthenticated etcd

Exposes etcd without authentication and installs `etcd-client` and `kubetcd` for direct cluster state access.

| Variable | Type | Description |
| -------- | ---- | ----------- |
| `unauth_etcd` | boolean | Expose etcd without authentication. In kubeadm multinode clusters, runs on control plane nodes only. Not supported with MicroK8s HA (multinode) as it uses dqlite instead of etcd |

### Anonymous Cluster Admin

Binds `cluster-admin` to `system:anonymous` via a ClusterRoleBinding. Combined with `enable_unauth_api`, any unauthenticated request gets full cluster access.

| Variable | Type | Description |
| -------- | ---- | ----------- |
| `anon_cluster_admin` | boolean | Bind `cluster-admin` to `system:anonymous` |

### Network Policies (MicroK8s only)

Enables Calico CNI and deploys a default-deny-all NetworkPolicy.

| Variable | Type | Description |
| -------- | ---- | ----------- |
| `enable_network_policies` | boolean | Enable Calico and deploy default-deny NetworkPolicy |

### Pod RCE

Deploys a Flask app with a command injection vulnerability via a ping endpoint.

| Variable | Type | Description |
| -------- | ---- | ----------- |
| `demo_pod_rce` | boolean | Deploy vulnerable ping app (NodePort 30100) |

### Kubelet Proxy Lateral Movement

Deploys a ClusterRole and attacker pod to demonstrate lateral movement via the `nodes/proxy` subresource.

| Variable | Type | Description |
| -------- | ---- | ----------- |
| `gh_nodes_proxy` | boolean | Deploy Kubelet proxy lateral movement scenario |

---

## Security Modules

### Pod Security Admission

Applies Kubernetes [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) labels to one or more namespaces. Each namespace is created if it does not already exist. Built into Kubernetes 1.25+, no additional controllers required.

Profiles: `privileged` (no restrictions), `baseline` (prevents known privilege escalations), `restricted` (heavily hardened).

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `enable_pod_security_admission` | boolean | Create and label all namespaces in `psa_namespaces` |
| `psa_namespaces` | list | Each entry: `name`, `enforce`, `audit`, `warn` (all default to `baseline`/`restricted`/`restricted`) |

```yaml
psa_namespaces:
  - name: prod
    enforce: restricted
    audit: restricted
    warn: restricted
  - name: staging
    enforce: baseline
```

### Custom RBAC

Creates namespaces, ServiceAccounts, Roles/ClusterRoles, and RoleBindings/ClusterRoleBindings from user-defined lists. Resources are created in dependency order.

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `enable_custom_rbac` | boolean | Enable the module |
| `rbac_namespaces` | list of strings | Namespaces to create |
| `rbac_service_accounts` | list | ServiceAccounts: `name`, `namespace` |
| `rbac_roles` | list | `Role`/`ClusterRole` objects: `kind`, `name`, `namespace` (Role only), `rules` |
| `rbac_bindings` | list | `RoleBinding`/`ClusterRoleBinding` objects: `kind`, `name`, `namespace` (RoleBinding only), `role_ref`, `subjects` |

```yaml
rbac_namespaces:
  - dev
rbac_service_accounts:
  - name: app-sa
    namespace: dev
rbac_roles:
  - kind: ClusterRole
    name: secret-reader
    rules:
      - apiGroups: [""]
        resources: ["secrets"]
        verbs: ["get", "list"]
rbac_bindings:
  - kind: ClusterRoleBinding
    name: secret-reader-binding
    role_ref:
      kind: ClusterRole
      name: secret-reader
    subjects:
      - kind: ServiceAccount
        name: app-sa
        namespace: dev
```

### Admission Controller (Kyverno)

Deploys [Kyverno](https://kyverno.io) as a validating or mutating admission webhook.

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `enable_admission_controller` | boolean | Deploy Kyverno |
| `kyverno_policy_type` | string | `validating` or `mutating` |
| `kyverno_policy_preset` | string | **Validating:** `block_privileged`, `require_labels`<br>**Mutating:** `inject_security_context`, `add_default_labels` |
| `kyverno_custom_policies` | list | Additional Kyverno policy manifests to apply (inline dicts) |
| `kyverno_excluded_namespaces` | list | Namespaces excluded from Kyverno policies (default: `kube-system`, `kyverno`, `falco`, `grafana`, `local-path-storage`) |
| `enable_malicious_webhook` | boolean | Deploy a Flask mutating webhook that injects a privileged init container into pods in namespaces labelled `webhook: enabled` |

### Headlamp Dashboard

Deploys [Headlamp](https://headlamp.dev) as an in-cluster Kubernetes dashboard. Creates a `headlamp-admin` service account bound to `cluster-admin` and prints a long-lived token at the end of the play.

Works with both `microk8s` and `kubeadm`.

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `enable_headlamp` | boolean | Deploy Headlamp |
| `headlamp_namespace` | string | Namespace (default: `kube-system`) |
| `headlamp_nodeport` | integer | NodePort for web UI (default: `30095`) |

### Custom Pods

Deploy arbitrary Kubernetes manifests — inline dicts or paths to YAML files.

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `custom_pods` | list | Each entry is an inline manifest dict or a path string to a YAML file |

---

## Attack Simulation Modules

### C2 Pod

Deploys a simulated C2 beacon pod that produces realistic network and syscall telemetry for Falco detection engineering. Requires a reachable Mythic C2 server.

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `enable_c2_pod` | boolean | Deploy the C2 agent pod |
| `c2_pod_namespace` | string | Namespace (default: `monitoring`) |
| `c2_pod_name` | string | Pod name (default: `app-monitor`) |
| `c2_pod_sa_permissions` | string | `minimal` — namespace-scoped read<br>`read-secrets` — cluster-wide read including secrets<br>`cluster-admin` — full cluster admin |
| `c2_callback_host` | string | Callback IP/hostname (defaults to `mythic_server_ip`) |
| `c2_callback_port` | integer | Callback port (defaults to `mythic_http_profile_port`) |
| `c2_callback_interval` | integer | Base beacon interval in seconds (default: `60`) |
| `c2_callback_jitter` | integer | Max random jitter in seconds (default: `20`) |

### Mythic C2 Server

Provisions a standalone Mythic C2 server VM with the Poseidon agent, HTTP profile, and a pre-built payload.

| Variable | Type | Options / Notes |
| -------- | ---- | --------------- |
| `mythic_server` | boolean | Install Mythic C2 on this VM (skips K8s install) |
| `mythic_server_ip` | string | IP of the Mythic VM — set on both the K8s node and the Mythic VM |
| `mythic_server_hostname` | string | Hostname of the Mythic VM for DNS resolution (default: `{{ range_id }}-mythic`) |
| `mythic_admin_user` | string | Web UI admin username (default: `mythic_admin`) |
| `mythic_admin_password` | string | Auto-generated; saved to `/tmp/.mythic_admin_password` |
| `mythic_http_profile_port` | integer | HTTP C2 listener port (default: `80`) |
| `mythic_version` | string | Pinned Mythic git tag (default: `master`) |

---

## Example Configs

### kubeadm cluster with Falco, Grafana, and unauthenticated attack surfaces

```yaml
ludus:
  - vm_name: "{{ range_id }}-k8s-kubeadm-01"
    hostname: "{{ range_id }}-k8s-kubeadm-01"
    template: ubuntu-24.04-x64-server-template
    vlan: 20
    ip_last_octet: 10
    ram_gb: 4
    cpus: 4
    linux: true
    roles:
      - install_k8s
      - telemetry
    role_vars:
      k8s_flavor: kubeadm
      kubeadm_version: "1.31"
      k8s_cni: calico
      enable_unauth_api: true
      enable_unauth_kubelet: true
      unauth_etcd: true
      falco_custom_rules:
        - "Anonymous Request Allowed"
        - "Anonymous Request Failed"
        - "Kubelet Remote Exec Attempt"
        - "ETCD Access"
      ui: grafana
```

### Mythic C2 server + K8s node with C2 beacon pod

```yaml
ludus:
  - vm_name: "{{ range_id }}-mythic"
    hostname: "{{ range_id }}-mythic"
    template: ubuntu-24.04-x64-server-template
    vlan: 20
    ip_last_octet: 20
    ram_gb: 8
    cpus: 4
    linux: true
    roles:
      - install_k8s
    role_vars:
      mythic_server: true
      mythic_server_ip: 10.X.20.20
      mythic_server_hostname: "{{ range_id }}-mythic"
      mythic_http_profile_port: 80

  - vm_name: "{{ range_id }}-k8s-01"
    hostname: "{{ range_id }}-k8s-01"
    template: ubuntu-24.04-x64-server-template
    vlan: 20
    ip_last_octet: 10
    ram_gb: 8
    cpus: 4
    linux: true
    roles:
      - install_k8s
      - telemetry
    role_vars:
      k8s_flavor: microk8s
      microk8s_addons:
        - dns
        - storage
        - helm3
      mythic_server_ip: 10.X.20.20
      mythic_server_hostname: "{{ range_id }}-mythic"
      enable_c2_pod: true
      c2_pod_sa_permissions: read-secrets
      ui: grafana
```

---

## Service Ports

| Service | Default NodePort | Notes |
| ------- | --------------- | ----- |
| Grafana | 30147 | Web dashboard; credentials `admin` / `admin`. Configurable via `grafana_nodeport` |
| Loki | 31000 | HTTP API |
| Falco k8saudit webhook | 30007 | Kubernetes audit event ingestion. Configurable via `falco_nodeport` |
| Falcosidekick web UI | 30088 | `ui: falcosidekick`; configurable via `falcosidekick_webui_nodeport` |
| Headlamp dashboard | 30095 | `enable_headlamp` module; token printed at play end |
| Vulnerable ping app (RCE) | 30100 | `demo_pod_rce` module |
| Mythic C2 web UI | 7443 | HTTPS; credentials saved to `/tmp/.mythic_admin_password` |
| Kubelet API | 10250 | Direct access when `enable_unauth_kubelet: true` |
