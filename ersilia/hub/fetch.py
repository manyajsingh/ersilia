"""Fetch model and dev it to a BentoML bundle"""

import os
import runpy
import shutil
from .. import ErsiliaBase
from ..utils.download import GitHubDownloader, OsfDownloader, PseudoDownloader
from ..utils.zip import Zipper


class ModelFetcher(ErsiliaBase):

    def __init__(self, config_json=None, overwrite=True, local=False):
        ErsiliaBase.__init__(self, config_json=config_json)
        self.token = self.cfg.HUB.TOKEN
        self.org = self.cfg.HUB.ORG
        self.tag = self.cfg.HUB.TAG
        self.overwrite = overwrite
        self.pseudo_down = PseudoDownloader(overwrite=overwrite)
        self.osf_down = OsfDownloader(overwrite=overwrite)
        self.github_down = GitHubDownloader(self.token) # TODO: add overwrite?
        self.zipper = Zipper(remove=True) # TODO: Add overwrite?
        self.local = local

    def _model_path(self, model_id):
        folder = os.path.join(self._dest_dir, model_id)
        return folder

    def _data_path(self, model_id):
        return os.path.join(self.cfg.LOCAL.DATA, model_id)

    def get_repo(self, model_id):
        """Download the model from GitHub"""
        folder = self._model_path(model_id)
        self.github_down.clone(org=self.org, repo=model_id, destination=folder)

    def get_model(self, model_id):
        """Create a ./model folder in the model repository"""
        folder = os.path.join(self._model_path(model_id), "model")
        if self.local:
            path = os.path.join(self._data_path(model_id), "model")
            self.pseudo_down.fetch(path, folder)
        else:
            path = os.path.join("models", model_id+".zip")
            self.osf_down.fetch(project_id=self.cfg.EXT.OSF_PROJECT, filename=path,
                                destination=self._dest_dir, tmp_folder=self._tmp_dir)
            self.zipper.unzip(os.path.join(self._dest_dir, model_id+".zip"), self._tmp_dir)
            src = os.path.join(self._tmp_dir, model_id)
            shutil.move(os.path.join(src, "model"), os.path.join(self._dest_dir, model_id))
            shutil.rmtree(src)

    def pack(self, model_id):
        """Pack model"""
        folder = self._model_path(model_id)
        pack_script = os.path.join(folder, self.cfg.HUB.PACK_SCRIPT)
        runpy.run_path(path_name=pack_script)

    def fetch(self, model_id):
        self.get_repo(model_id)
        self.get_model(model_id)
        self.pack(model_id)
