# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : MeUtils.
# @File         : Bert
# @Time         : 2020/11/20 2:59 下午
# @Author       : yuanjie
# @Email        : yuanjie@xiaomi.com
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *

os.environ['TF_KERAS'] = '1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf

tf.get_logger().setLevel(40)  # logging.ERROR

from meutils.np_utils import normalize
from meutils.path_utils import get_module_path

import zipfile
from bert4keras.backend import keras
from bert4keras.models import build_transformer_model
from bert4keras.tokenizers import Tokenizer
from bert4keras.snippets import sequence_padding


class Bert4Vec(object):

    def __init__(self, bert_dir=None):

        if bert_dir is None:
            bert_dir = 'chinese_roformer-sim-char-ft_L-6_H-384_A-6'

        if not Path(bert_dir).is_dir():
            logger.info("下载预训练模型")
            url = f'https://open.zhuiyi.ai/releases/nlp/models/zhuiyi/{bert_dir}.zip'
            filename = wget.download(url)

            assert zipfile.is_zipfile(filename)
            zipfile.ZipFile(filename).extractall()
        logger.info(bert_dir)

        self.dict_path = f"{bert_dir}/vocab.txt"
        self.config_path = f"{bert_dir}/bert_config.json"
        self.checkpoint_path = f"{bert_dir}/bert_model.ckpt"

        self.tokenizer = Tokenizer(self.dict_path, do_lower_case=True)

        # 建立加载模型
        logger.info("BuildingModel")
        model_name = 'roformer' if 'roformer' in bert_dir else 'bert'

        self._bert = build_transformer_model(
            self.config_path,
            self.checkpoint_path,
            model=model_name,
            with_pool='linear',
            application='unilm',
            return_keras_model=False  # True: bert.predict([np.array([token_ids]), np.array([segment_ids])])
        )

        self.encoder = keras.models.Model(self._bert.model.inputs, self._bert.model.outputs[0])
        # self._seq2seq = keras.models.Model(self._bert.model.inputs, self._bert.model.outputs[1])

    def encode(self, sentences='万物皆可embedding', maxlen=256, batch_size=1000, decimals=6, return_list=True):
        """自行设计缓存"""
        if isinstance(sentences, str):
            sentences = [sentences]

        assert isinstance(sentences, (tuple, list))

        data = self.sentences2seq(sentences=map(str, sentences), maxlen=maxlen)
        vecs = normalize(np.round(self.encoder.predict(data, batch_size=batch_size), decimals))
        return vecs.tolist() if return_list else vecs

    def sentences2seq(self, sentences, maxlen=64):
        batch_token_ids, batch_segment_ids = [], []
        for s in sentences:
            token_ids, segment_ids = self.tokenizer.encode(s, maxlen=maxlen)
            batch_token_ids.append(token_ids)
            batch_segment_ids.append(segment_ids)
        batch_token_ids = sequence_padding(batch_token_ids)
        batch_segment_ids = sequence_padding(batch_segment_ids)
        return batch_token_ids, batch_segment_ids


if __name__ == '__main__':
    BERT_HOME = "/Users/yuanjie/Downloads/chinese_roformer-sim-char-ft_L-6_H-384_A-6"
    s2v = Bert4Vec(BERT_HOME)
    print(s2v.encode(['万物皆向量']))

    from appzoo import App

    app = App()
    app.add_route('/simbert', s2v.encode, result_key='vectors', method='POST')
    app.run(access_log=False)
