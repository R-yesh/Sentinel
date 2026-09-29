import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ...schemas.sentinel import (
    ComponentObservation, ComponentPage, InvestigationRequest, InvestigationResponse,
)
from ...services.datasets import (
    DatasetRepository, DatasetUnavailable, SelectionNotFound, get_dataset_repository,
)
from ...services.investigations import InvalidLotContext, investigate
from ...schemas.population import PopulationResponse
from ...services.population import population
from ...schemas.evaluation import EvaluationResponse
from ...services.evaluation import evaluation


router = APIRouter(prefix="/api/v1", tags=["Sentinel"])
logger = logging.getLogger(__name__)
Repository = Annotated[DatasetRepository, Depends(get_dataset_repository)]


@router.get('/datasets/{dataset_id}/evaluation', response_model=EvaluationResponse)
def get_evaluation(dataset_id: str, repository: Repository):
    try:
        return evaluation(repository, dataset_id)
    except SelectionNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except DatasetUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get('/datasets/{dataset_id}/population', response_model=PopulationResponse)
def get_population(dataset_id: str, repository: Repository):
    try:
        return population(repository, dataset_id)
    except SelectionNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except DatasetUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get("/datasets/{dataset_id}/components", response_model=ComponentPage)
def list_components(
    dataset_id: str,
    repository: Repository,
    search: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    try:
        return repository.list_components(dataset_id, search, page, page_size)
    except SelectionNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except DatasetUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get(
    "/datasets/{dataset_id}/components/{component_id}",
    response_model=ComponentObservation,
)
def get_component(dataset_id: str, component_id: str, repository: Repository):
    try:
        return repository.component(repository.load(dataset_id), component_id)
    except SelectionNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except DatasetUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@router.post("/investigations", response_model=InvestigationResponse)
def create_investigation(selection: InvestigationRequest, repository: Repository):
    try:
        return investigate(repository, selection.dataset_id, selection.component_id)
    except SelectionNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except DatasetUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except InvalidLotContext as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        logger.exception("Sentinel investigation failed")
        raise HTTPException(
            502, "Sentinel could not complete the investigation. Check server dependencies and logs.",
        ) from exc
