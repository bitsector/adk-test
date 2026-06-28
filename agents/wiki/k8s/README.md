# Wiki agent on kind (Phase 0)

Run the containerized wiki agent in a local Kubernetes cluster ([kind](https://kind.sigs.k8s.io/)).
This phase is a single pod with ADK's default local SQLite — just enough to prove
the agent runs in k8s. The shared-DB / multi-pod work comes in a later phase.

## How it differs from the voice agent

- **Backend**: wiki runs on the plain **AI Studio (API-key)** backend — no Vertex
  AI, no service account. The only secret is `GOOGLE_API_KEY`, injected as an env
  var from a Secret (not a mounted file). The manifest deliberately leaves
  `GOOGLE_GENAI_USE_VERTEXAI` **unset** — setting it would flip wiki onto Vertex
  and then demand an SA key.
- **Port**: maps host `:8000` -> node `:30080` -> pod `:8000`. The voice cluster
  maps the same host port, so only one cluster can run at a time — `kind delete
  cluster --name voice` first (and stop any local `docker run -p 8000:8000`).
- **No mic constraint**: wiki is text-only, so there's no `getUserMedia` /
  secure-context requirement — `http://<lan-ip>:8000` works for remote browsers too.

## Run it

```bash
# 0. Build the image if you haven't (from the repo root):
docker build -f agents/wiki/Dockerfile -t wiki-agent:latest .

# 1. Create the cluster:
kind create cluster --config agents/wiki/k8s/kind-cluster.yaml

# 2. Load the local image into the cluster's node (kind can't see your Docker
#    daemon). NOTE: `kind load docker-image` fails on this Docker 29 / kind combo
#    with "unknown containerd config version: 4" — import the tar straight into
#    the node's containerd (k8s.io = the namespace kubelet reads) instead:
docker save wiki-agent:latest | \
  docker exec -i wiki-control-plane ctr --namespace=k8s.io images import -
# verify: docker exec wiki-control-plane ctr -n k8s.io images ls | grep wiki-agent

# 3. Create the API key as a Secret (NOT baked into any image/manifest).
#    Source .env first so $GOOGLE_API_KEY is in the shell:
set -a; source .env; set +a
kubectl create secret generic wiki-agent-secrets \
  --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY"

# 4. Deploy + Service:
kubectl apply -f agents/wiki/k8s/deployment.yaml

# 5. Wait until it's ready:
kubectl rollout status deploy/wiki-agent

# 6. Open the dev UI and pick "wiki":
#    http://localhost:8000
```

> `kubectl` talks to whichever cluster is the current context. After `kind create
> cluster` the context is switched to `kind-wiki` automatically; if you've since
> touched another cluster, re-select it: `kubectl config use-context kind-wiki`.

## Debug / teardown

```bash
kubectl get pods -l app=wiki-agent
kubectl logs -l app=wiki-agent -f
kubectl describe pod -l app=wiki-agent     # if it won't start (e.g. missing Secret)

kind delete cluster --name wiki
```

## Notes

- The image runs as non-root `appuser` (uid/gid 999); the manifest's
  `securityContext` matches that. No `fsGroup` is needed (wiki mounts no Secret
  file — the key comes in as an env var).
- After rebuilding the image, re-run step 2 (`kind load ...`) and restart the
  rollout: `kubectl rollout restart deploy/wiki-agent`.
- `imagePullPolicy: IfNotPresent` ensures the kind-loaded image is used instead of
  trying to pull `wiki-agent:latest` from a registry.
- If the dev UI won't connect at all — the request just hangs with no access-log
  line — it's the NordVPN kill switch blocking host↔container traffic. Fix:
  `nordvpn set lan-discovery enable`.
