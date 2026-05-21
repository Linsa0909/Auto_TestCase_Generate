#!/bin/bash
# ==========================================
#  Test Case Intelligence - K8s Venus 部署
#  kubectl apply 一键部署，NodePort 30105
# ==========================================
set -e

K8S_YAML="$(dirname "$0")/k8s-deploy.yaml"
NAMESPACE="test-case-intel"

echo "=========================================="
echo "  Test Case Intelligence → K8s (Venus)"
echo "=========================================="
echo ""

# 1. 检查 kubectl
if ! command -v kubectl &>/dev/null; then
    echo "[ERROR] kubectl 未安装，请先安装"
    exit 1
fi

# 2. 部署
echo ">>> 部署到 K8s..."
kubectl apply -f "${K8S_YAML}"

# 3. 等待就绪
echo ""
echo ">>> 等待 Pod 就绪..."
kubectl wait --for=condition=ready pod \
    -l app=test-case-intel \
    -n "${NAMESPACE}" \
    --timeout=120s

echo ""
echo "=========================================="
echo "  部署完成"
echo "  访问地址: http://<节点IP>:30105"
echo "  API 文档: http://<节点IP>:30105/docs"
echo "=========================================="
echo ""
echo "  查看 Pod:    kubectl get pod -n ${NAMESPACE}"
echo "  查看日志:    kubectl logs -f -l app=test-case-intel -n ${NAMESPACE}"
echo "  重新部署:    kubectl rollout restart deployment/test-case-intel -n ${NAMESPACE}"
echo "  卸载:        kubectl delete -f ${K8S_YAML}"
