from mlflow_export_import.model.export_model import ModelExporter
from mlflow_export_import.model.import_model import ModelImporter
import utils_test 
from compare_utils import compare_models
from init_tests import mlflow_context
from mlflow_export_import.model.import_model import _extract_model_path


def test_export_import_model(mlflow_context):
    run_src = _create_run(mlflow_context.client_src)
    exporter = ModelExporter(mlflow_context.client_src)
    model_name_src = utils_test.mk_test_object_name_default()
    model_src = mlflow_context.client_src.create_registered_model(model_name_src)
    source = f"{run_src.info.artifact_uri}/model"
    mlflow_context.client_src.create_model_version(model_name_src, source, run_src.info.run_id)
    exporter.export_model(model_name_src, mlflow_context.output_dir)

    model_name_dst = utils_test.create_dst_model_name(model_name_src)
    experiment_name =  model_name_dst
    importer = ModelImporter(mlflow_context.client_dst)
    importer.import_model(model_name_dst, mlflow_context.output_dir, experiment_name, delete_model=True, verbose=False, sleep_time=10)
    model_dst = mlflow_context.client_dst.get_registered_model(model_name_dst)

    model_src = mlflow_context.client_src.get_registered_model(model_name_src)
    assert len(model_src.latest_versions) == len(model_dst.latest_versions)

    compare_models(mlflow_context.client_src, mlflow_context.client_dst, model_src, model_dst, mlflow_context.output_dir)


def test_export_import_model_stages(mlflow_context):
    exporter = ModelExporter(mlflow_context.client_src, stages=["Production","Staging"])
    model_name_src = utils_test.mk_test_object_name_default()
    model_src = mlflow_context.client_src.create_registered_model(model_name_src)

    _create_version(mlflow_context.client_src, model_name_src, "Production")
    _create_version(mlflow_context.client_src, model_name_src, "Staging")
    _create_version(mlflow_context.client_src, model_name_src, "Archived")
    exporter.export_model(model_name_src, mlflow_context.output_dir)

    model_name_dst = utils_test.create_dst_model_name(model_name_src)
    experiment_name =  model_name_dst
    importer = ModelImporter(mlflow_context.client_dst)
    importer.import_model(model_name_dst, 
        mlflow_context.output_dir, 
        experiment_name, delete_model=True, 
        verbose=False, 
        sleep_time=10)
    model_dst = mlflow_context.client_dst.get_registered_model(model_name_dst)
    assert len(model_dst.latest_versions) == 2
    compare_models(mlflow_context.client_src, mlflow_context.client_dst,  model_src, model_dst, mlflow_context.output_dir)


def _create_version(client, model_name, stage=None):
    run = _create_run(client)
    source = f"{run.info.artifact_uri}/model"
    vr = client.create_model_version(model_name, source, run.info.run_id)
    if stage:
        vr = client.transition_model_version_stage(model_name, vr.version, stage)
    return vr


def _create_run(client):
    _, run = utils_test.create_simple_run(client)
    return client.get_run(run.info.run_id)


# Simple tests for parsing

_run_id = "48cf29167ddb4e098da780f0959fb4cf"
_model_path = "models:/my_model"


def test_extract_model_path_databricks(mlflow_context):
    source = f"dbfs:/databricks/mlflow-tracking/4072937019901104/{_run_id}/artifacts/{_model_path}"
    _run_test_extract_model_path(source)


def test_extract_model_path_oss(mlflow_context):
    source = f"/opt/mlflow_context/local_mlrun/mlruns/3/{_run_id}/artifacts/{_model_path}"
    _run_test_extract_model_path(source)


def _run_test_extract_model_path(source):
    model_path2 = _extract_model_path(source, _run_id)
    assert _model_path == model_path2