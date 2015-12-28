# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import pytest
from bosonnlp import BosonNLP, ClusterTask, CommentsTask
from bosonnlp.exceptions import HTTPError, TimeoutError


def test_invalid_token_raises_HTTPError():
    nlp = BosonNLP('invalid token')
    pytest.raises(HTTPError, lambda: nlp.sentiment('美好的世界'))


@pytest.fixture(scope='module',
                params=[{}])
def nlp(request):
    # 注意：在测试时请设置环境变量BOSON_API_TOKEN为您的 API token。
    return BosonNLP(os.environ['BOSON_API_TOKEN'], **request.param)

def test_sentiment(nlp):
    result = nlp.sentiment(['再也不来了', '美好的世界'])
    assert result[0][1] > result[0][0]
    assert result[1][0] > result[1][1]


def test_convert_time_no_basetime(nlp):
    result = nlp.convert_time("2013年二月二十八日下午四点三十分二十九秒")
    assert result.get("timestamp") == "2013-02-28 16:30:29"


def test_convert_time_with_basetime(nlp):
    result = nlp.convert_time("2013年二月二十八日下午四点三十分二十九秒",
                              1408674823)
    assert result.get("timestamp") == "2013-02-28 16:30:29"


def test_convert_time_with_datetime(nlp):
    import datetime
    result = nlp.convert_time("2013年二月二十八日下午四点三十分二十九秒",
                              datetime.datetime.today())
    assert result.get("timestamp") == "2013-02-28 16:30:29"


def test_compress_request_body_larger_than_10k(nlp):
    resp = nlp._api_request('POST', '/sentiment/analysis',
                            data=''.join(['美好的世界'] * 800))
    assert resp.ok
    assert resp.request.headers['Content-Encoding'] == 'gzip'


def test_exceed_maximum_size_of_100_raises_HTTPError(nlp):
    input = ['今天天气好'] * 101
    excinfo = pytest.raises(HTTPError, lambda: nlp.sentiment(input))
    assert excinfo.value.response.status_code == 413


def test_classify(nlp):
    assert nlp.classify('俄否决安理会谴责叙军战机空袭阿勒颇平民') == [5]
    assert nlp.classify(['俄否决安理会谴责叙军战机空袭阿勒颇平民',
                         '邓紫棋谈男友林宥嘉：我觉得我比他唱得好',
                         'Facebook收购印度初创公司']) == [5, 4, 8]


def test_suggest(nlp):
    assert nlp.suggest('北京', top_k=2)[1][1] == '上海/ns'


def test_extract_keywords(nlp):
    assert len(nlp.extract_keywords('病毒式媒体网站：让新闻迅速蔓延', top_k=5)) == 5


def test_depparser(nlp):
    assert nlp.depparser('今天天气好') == \
        [{'tag': ['NT', 'NN', 'VA'],
          'role': ['TMP', 'SBJ', 'ROOT'],
          'head': [2, 2, -1],
          'word': ['今天', '天气', '好']}]
    assert nlp.depparser(['今天天气好', '美好的世界']) == \
        [{'tag': ['NT', 'NN', 'VA'],
          'role': ['TMP', 'SBJ', 'ROOT'],
          'head': [2, 2, -1],
          'word': ['今天', '天气', '好']},
         {'tag': ['VA', 'DEC', 'NN'],
          'role': ['DEC', 'NMOD', 'ROOT'],
          'head': [1, 2, -1],
          'word': ['美好', '的', '世界']}]


def test_ner(nlp):
    assert nlp.ner('成都商报记者 姚永忠', sensitivity=2) == \
        [{'entity': [[0, 2, 'product_name'],
                     [2, 3, 'job_title'],
                     [3, 4, 'person_name']],
          'tag': ['ns', 'n', 'n', 'nr'],
          'word': ['成都', '商报', '记者', '姚永忠']}]

    assert nlp.ner(['成都商报记者 姚永忠', '微软XP操作系统今日正式退休'], sensitivity=2) == \
        [{'entity': [[0, 2, 'product_name'],
                     [2, 3, 'job_title'],
                     [3, 4, 'person_name']],
          'tag': ['ns', 'n', 'n', 'nr'],
          'word': ['成都', '商报', '记者', '姚永忠']},

         {'entity': [[0, 2, 'product_name'],
                     [3, 4, 'time']],
          'tag': ['nz', 'nx', 'nl', 't', 'ad', 'v'],
          'word': ['微软', 'XP', '操作系统', '今日', '正式', '退休']}]


def test_tag(nlp):
    assert nlp.tag('成都商报记者 姚永忠') == \
        [{'word': ['成都', '商报', '记者', '姚永忠'],
          'tag': ['ns', 'n', 'n', 'nr']}]

    assert nlp.tag(['成都商报记者 姚永忠', '微软XP操作系统今日正式退休']) == \
        [{'word': ['成都', '商报', '记者', '姚永忠'],
          'tag': ['ns', 'n', 'n', 'nr']},

         {'word': ['微软', 'XP', '操作系统', '今日', '正式', '退休'],
          'tag': ['nz', 'nx', 'nl', 't', 'ad', 'v']}]


def test_summary(nlp):
    content = (
        '腾讯科技讯（刘亚澜）10月22日消息，前优酷土豆技术副总裁'
        '黄冬已于日前正式加盟芒果TV，出任CTO一职。'
        '资料显示，黄冬历任土豆网技术副总裁、优酷土豆集团产品'
        '技术副总裁等职务，曾主持设计、运营过优酷土豆多个'
        '大型高容量产品和系统。'
        '此番加入芒果TV或与芒果TV计划自主研发智能硬件OS有关。')

    title = '前优酷土豆技术副总裁黄冬加盟芒果TV任CTO'

    assert (nlp.summary(title, content) ==
            '腾讯科技讯（刘亚澜）10月22日消息，前优酷土豆技术副总裁黄冬'
            '已于日前正式加盟芒果TV，出任CTO一职。')

    assert (nlp.summary(title, content, word_limit=0.4, not_exceed=True) ==
            '腾讯科技讯（刘亚澜）10月22日消息，前优酷土豆技术副总裁黄冬'
            '已于日前正式加盟芒果TV，出任CTO一职。')


def test_cluster_task_wait_until_complete_raises_TimeoutError(nlp):
    input = ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
             '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦']
    cluster = nlp.create_cluster_task(input)
    cluster.analysis()
    pytest.raises(TimeoutError, lambda: cluster.wait_until_complete(timeout=0.1))


@pytest.mark.parametrize('input', [
    ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
     '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'],

    [(idx + 1, text) for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'])],

    [{'_id': idx + 1, 'text': text} for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'])],

])
def test_cluster(nlp, input):
    result = nlp.cluster(input)
    assert result[0]['num'] == 2


@pytest.mark.parametrize('input', [
    ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
     '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'],

    [(idx + 1, text) for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'])],

    [{'_id': idx + 1, 'text': text} for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'])],

])
def test_cluster_task(nlp, input):
    cluster = ClusterTask(nlp, contents=input)
    cluster.analysis()
    cluster.wait_until_complete()
    result = cluster.result()
    cluster.clear()
    assert result[0]['num'] == 2
    assert type(cluster._contents[0]) == dict
    assert len(cluster._contents) == 7


@pytest.mark.parametrize('input', [
    ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
     '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'],

    [(idx + 1, text) for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'])],

    [{'_id': idx + 1, 'text': text} for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'])],
])
def test_create_cluster_task(nlp, input):
    cluster = nlp.create_cluster_task(input)
    cluster.analysis()
    cluster.wait_until_complete()
    result = cluster.result()
    cluster.clear()
    assert result[0]['num'] == 2
    assert type(cluster._contents[0]) == dict
    assert len(cluster._contents) == 7


@pytest.mark.parametrize('input1,input2', [
    (['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨'],
     ['重重江外平湖', '当年戏马会东徐', '今日凄凉南浦']),

    ([(idx + 1, text) for idx, text in enumerate(['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨'])],
     [(idx + 1 + 4, text) for idx, text in enumerate(['重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'])]),

    ([{'_id': idx + 1, 'text': text} for idx, text in enumerate(['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨'])],
     [{'_id': idx + 1 + 4, 'text': text} for idx, text in enumerate(['重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'])]),
])
def test_cluster_task_with_multiple_push(nlp, input1, input2):
    cluster = nlp.create_cluster_task()
    cluster.push(input1)
    cluster.push(input2)
    cluster.analysis()
    cluster.wait_until_complete()
    result = cluster.result()
    cluster.clear()
    assert result[0]['num'] == 2
    assert type(cluster._contents[0]) == dict
    assert len(cluster._contents) == 7


@pytest.mark.parametrize('input', [
    ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
     '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2,

    [(idx + 1, text) for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2)],

    [{'_id': idx + 1, 'text': text} for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2)],

])
def test_comments(nlp, input):
    result = nlp.comments(input)
    assert len(result) == 4
    assert {'opinion', '_id', 'list', 'num'} == set(result[0].keys())


@pytest.mark.parametrize('input', [
    ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
     '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2,

    [(idx + 1, text) for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2)],

    [{'_id': idx + 1, 'text': text} for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2)],

])
def test_comments_task(nlp, input):
    comments = CommentsTask(nlp, contents=input)
    comments.analysis()
    comments.wait_until_complete()
    result = comments.result()
    comments.clear()
    assert len(result) == 4
    assert {'opinion', '_id', 'list', 'num'} == set(result[0].keys())


@pytest.mark.parametrize('input', [
    ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
     '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2,

    [(idx + 1, text) for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2)],

    [{'_id': idx + 1, 'text': text} for idx, text in enumerate(
        ['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨',
         '重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2)],
])
def test_create_comments_task(nlp, input):
    comments = nlp.create_comments_task(input)
    comments.analysis()
    comments.wait_until_complete()
    result = comments.result()
    comments.clear()
    assert len(result) == 4
    assert {'opinion', '_id', 'list', 'num'} == set(result[0].keys())


@pytest.mark.parametrize('input1,input2', [
    (['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨'] * 2,
     ['重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2),

    ([(idx + 1, text) for idx, text in enumerate(['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨'] * 2)],
     [(idx + 1 + 8, text) for idx, text in enumerate(['重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2)]),

    ([{'_id': idx + 1, 'text': text} for idx, text in enumerate(['今天天气好', '今天天气好', '今天天气不错', '点点楼头细雨'] * 2)],
     [{'_id': idx + 1 + 8, 'text': text} for idx, text in enumerate(['重重江外平湖', '当年戏马会东徐', '今日凄凉南浦'] * 2)]),
])
def test_comments_task_with_multiple_push(nlp, input1, input2):
    comments = nlp.create_comments_task()
    comments.push(input1)
    comments.push(input2)
    comments.analysis()
    comments.wait_until_complete()
    result = comments.result()
    comments.clear()
    assert len(result) == 4
    assert {'opinion', '_id', 'list', 'num'} == set(result[0].keys())
