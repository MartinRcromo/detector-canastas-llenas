"""
Endpoint para consultar el cluster de un cliente
GET /api/cluster/{cuit}
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import execute_query

router = APIRouter()


class ClusterResponse(BaseModel):
    """Respuesta del endpoint /api/cluster/{cuit}"""
    cuit: str
    cliente: str
    empresa: str
    cluster_mix: str
    cluster_especial: str
    top1_rubro: str
    top1_share: float


@router.get("/api/cluster/{cuit}", response_model=ClusterResponse)
async def get_cluster(cuit: str):
    """
    Obtiene el cluster de un cliente desde la tabla cliente_cluster_v2

    Args:
        cuit: CUIT del cliente

    Returns:
        ClusterResponse con información del cluster

    Raises:
        HTTPException 404: Si el cliente no tiene cluster calculado
    """
    try:
        query = """
            SELECT
                cuit,
                cliente,
                empresa,
                cluster_mix,
                cluster_especial,
                top1_rubro,
                top1_share
            FROM cliente_cluster_v2
            WHERE cuit = :cuit
            LIMIT 1
        """

        result = execute_query(query, {"cuit": cuit})

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró cluster para el CUIT {cuit}. "
                       f"Ejecuta el script de clustering primero."
            )

        cluster_data = result[0]

        return ClusterResponse(
            cuit=cluster_data["cuit"],
            cliente=cluster_data["cliente"] or "Sin nombre",
            empresa=cluster_data["empresa"],
            cluster_mix=cluster_data["cluster_mix"],
            cluster_especial=cluster_data["cluster_especial"],
            top1_rubro=cluster_data["top1_rubro"],
            top1_share=float(cluster_data.get("top1_share", 0) or 0)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener cluster: {str(e)}"
        )
