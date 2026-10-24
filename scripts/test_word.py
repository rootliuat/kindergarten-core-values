"""
[INPUT]: 排版样例、build_word.cjs、check_word.xml_check 与可用 Node.js。
[OUTPUT]: 有效生成、标题空白定向规范、错误输入拒绝、损坏文档识别的回归结果。
[POS]: scripts 的结构与排版接口测试，不测试教学效果。
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from check_word import NS, W, xml_check
from environment import ROOT


class WordContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which('node')
        if not cls.node:
            raise RuntimeError('未找到 Node.js')
        cls.temp = tempfile.TemporaryDirectory(prefix='curriculum-test-')
        cls.folder = Path(cls.temp.name)
        cls.data = json.loads((ROOT/'references/sample-input.json').read_text('utf-8'))
        result, cls.doc = cls.build(cls.data, 'valid')
        if result.returncode:
            raise RuntimeError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def build(cls, data, name):
        source, doc = cls.folder/(name+'.json'), cls.folder/(name+'.docx')
        source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        result = subprocess.run([cls.node, str(ROOT/'scripts/build_word.cjs'), str(source), str(doc)],
                                capture_output=True, encoding='utf-8', timeout=30)
        return result, doc

    def test_valid_tables_and_text(self):
        errors, _, text, _ = xml_check(self.doc)
        self.assertEqual(errors, [])
        self.assertIn('寻找线索', text)
        self.assertIn('图片与成人转述', text)
        with ZipFile(self.doc) as archive:
            root = ET.fromstring(archive.read('word/document.xml'))
        tables = root.findall('.//w:tbl', NS)
        self.assertEqual([len(t.find('w:tr', NS).findall('w:tc', NS)) for t in tables], [4, 2, 3])
        self.assertEqual(len(tables[0].findall('w:tr', NS)), 1)
        self.assertEqual(len(tables[0].findall('.//w:shd', NS)), 4)

    def test_invalid_input_rejected(self):
        cases = []
        old = copy.deepcopy(self.data); old['sections'].pop(1); cases.append(old)
        missing = copy.deepcopy(self.data); missing['sections'][2]['blocks'] = [{'text': '没有脉络'}]; cases.append(missing)
        short = copy.deepcopy(self.data); short['sections'][2]['blocks'][0]['roadmap'].pop(); cases.append(short)
        empty = copy.deepcopy(self.data); empty['sections'][2]['blocks'][0]['roadmap'][0]['activities'] = []; cases.append(empty)
        moved = copy.deepcopy(self.data); moved['sections'][3]['blocks'].append(moved['sections'][2]['blocks'].pop()); cases.append(moved)
        uneven = copy.deepcopy(self.data); uneven['sections'][4]['blocks'][1]['table'][1].pop(); cases.append(uneven)
        for index, data in enumerate(cases):
            with self.subTest(index=index):
                result, output = self.build(data, f'invalid-{index}')
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())

    def test_heading_spacing_only(self):
        data = copy.deepcopy(self.data)
        headings = ['1.  整理 想法', '2.\t试一试', '3.\u3000再看看', '4.\u00a0回看', '5.已规范']
        blocks = [{'level': 3, 'text': text} for text in headings]
        blocks += [{'text': '1. 正文空格 保留'}, {'level': 2, 'text': '（一） 阶段空格保留'},
                   {'text': '网址说明', 'url': 'https://example.com/a.b'}]
        data['sections'][3]['blocks'].extend(blocks)
        result, doc = self.build(data, 'heading-spacing')
        self.assertEqual(result.returncode, 0, result.stderr)
        errors, _, text, _ = xml_check(doc)
        self.assertEqual(errors, [])
        for expected in ['1.整理 想法', '2.试一试', '3.再看看', '4.回看', '5.已规范',
                         '1. 正文空格 保留', '（一） 阶段空格保留']:
            self.assertIn(expected, text)
        saved = json.loads((self.folder/'heading-spacing.json').read_text('utf-8'))
        self.assertEqual(saved, data)
        with ZipFile(doc) as archive:
            self.assertIn('https://example.com/a.b', archive.read('word/_rels/document.xml.rels').decode())

    def corrupt(self, name, change):
        target = self.folder/(name+'.docx')
        with ZipFile(self.doc) as source, ZipFile(target, 'w') as output:
            for item in source.infolist():
                content = source.read(item.filename)
                if item.filename == 'word/document.xml':
                    tree = ET.fromstring(content)
                    change(tree)
                    content = ET.tostring(tree, encoding='utf-8')
                output.writestr(item, content)
        return xml_check(target)[0]

    def test_checker_detects_broken_roadmap(self):
        def remove_cell(tree):
            row = tree.find('.//w:tbl/w:tr', NS)
            row.remove(row.findall('w:tc', NS)[-1])
        self.assertIn('脉络表应为四列', self.corrupt('short-map', remove_cell))

    def test_checker_detects_wrong_font(self):
        def change_font(tree):
            tree.find('.//w:rFonts', NS).set(W+'eastAsia', 'Arial')
        self.assertTrue(any(e.startswith('字体：') for e in self.corrupt('font', change_font)))

    def test_checker_detects_heading_gap(self):
        for gap in (' ', '\u3000', '\t'):
            with self.subTest(gap=repr(gap)):
                def add_gap(tree):
                    for p in tree.findall('.//w:body/w:p', NS):
                        style = p.find('w:pPr/w:pStyle', NS)
                        if style is not None and style.get(W+'val') == 'h3':
                            run = p.find('w:r', NS)
                            text = run.find('w:t', NS)
                            text.text = '1.' + (gap + '活动' if gap != '\t' else '')
                            if gap == '\t':
                                ET.SubElement(run, W+'tab')
                                ET.SubElement(run, W+'t').text = '活动'
                            return
                    self.fail('样例缺少三级标题')
                errors = self.corrupt('heading-gap', add_gap)
                self.assertTrue(any(e.startswith('三级标题编号后不应留空白') for e in errors))


if __name__ == '__main__':
    unittest.main(verbosity=2)
