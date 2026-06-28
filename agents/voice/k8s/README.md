# Voice agent on kind (Phase 0)

Run the containerized voice agent in a local Kubernetes cluster ([kind](https://kind.sigs.k8s.io/)).
This phase is a single pod with ADK's default local SQLite — just enough to prove
the agent runs in k8s. The shared-DB / multi-pod work comes in a later phase.

## How it's exposed (and why not a LoadBalancer / Ingress)

- **LoadBalancer** — kind has no cloud provider, so a `LoadBalancer` Service stays
  `<pending>` forever (you'd need MetalLB or `cloud-provider-kind`). Skipped.
- **Ingress** — needs you to install a controller (nginx, etc.) first. Overkill for
  one pod.
- **NodePort + `extraPortMappings`** ← what we use. The kind-native, simplest path:
  the kind config maps host `:8000` to the node's `:30080`, and the NodePort Service
  listens there. `listenAddress: "0.0.0.0"` makes it LAN-reachable.

> ⚠️ For actual **voice** testing, open `http://localhost:8000` **on this host**.
> The mic (`getUserMedia`) needs a secure context — a remote browser over plain
> `http://<lan-ip>:8000` will connect but get no mic. Remote access needs HTTPS.

## Run it

```bash
# 0. Build the image if you haven't (from the repo root):
docker build -f agents/voice/Dockerfile -t voice-agent:latest .

# 1. Create the cluster:
kind create cluster --config agents/voice/k8s/kind-cluster.yaml

# 2. Load the local image into the cluster (kind can't see your Docker daemon):
kind load docker-image voice-agent:latest --name voice

# 3. Create the Vertex SA key as a Secret (NOT baked into any image/manifest):
kubectl create secret generic voice-agent-sa \
  --from-file=sa.json=secrets/voice-agent-sa-key.json

# 4. Deploy + Service:
kubectl apply -f agents/voice/k8s/deployment.yaml

# 5. Wait until it's ready:
kubectl rollout status deploy/voice-agent

# 6. Open the dev UI:
#    http://localhost:8000   (localhost = secure context, mic works)
```

## Debug / teardown

```bash
kubectl get pods -l app=voice-agent
kubectl logs -l app=voice-agent -f
kubectl describe pod -l app=voice-agent     # if it won't start (e.g. missing Secret)

kind delete cluster --name voice
```

## Notes

- The image runs as non-root `appuser` (uid/gid 999); the manifest's
  `securityContext` matches that and `fsGroup: 999` makes the mounted SA Secret
  readable.
- After rebuilding the image, re-run step 2 (`kind load ...`) and restart the
  rollout: `kubectl rollout restart deploy/voice-agent`.
- `imagePullPolicy: IfNotPresent` ensures the kind-loaded image is used instead of
  trying to pull `voice-agent:latest` from a registry.
