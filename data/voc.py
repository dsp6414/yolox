import os
import xml.etree.ElementTree as ET

from absl import app, flags, logging

FLAGS = flags.FLAGS

flags.DEFINE_string('voc_path', None, 'path to voc dataset')
flags.DEFINE_string('name_path', None, 'path to voc name file')
flags.DEFINE_string('txt_output_path', None, 'path to output txt file')
flags.DEFINE_enum('version', '07+12', ['07', '12', '07+12'], 'dataset version')
flags.DEFINE_bool('use_difficult', False, 'use difficult annotation')


def convert(voc_path, voc_name_path, txt_output_path, version, use_difficult=False):
    """
    - VOC
        - VOC2007
            - Annotations
            - ImageSets
                - Main
            - JPEGImages
        - VOC2012
            - Annotations
            - ImageSets
                - Main
            - JPEGImages

    :param voc_path:
    :param version: '07', '12', '07+12'
    :param use_difficult:
    :return: num_trainval, num_test
    """

    def _read_voc_txt(path):
        with open(path, 'r') as f:
            txt = f.readlines()

        return [line.strip() for line in txt]

    trainval_img_path = []
    trainval_ann_path = []
    test_img_path = []
    test_ann_path = []
    if version == '07' or version == '07+12':
        img_idx_path = os.path.join(voc_path, 'VOC2007', 'ImageSets', 'Main', 'trainval.txt')
        img_idx = _read_voc_txt(img_idx_path)
        trainval_img_path.extend([os.path.join(voc_path, 'VOC2007', 'JPEGImages', idx + '.jpg') for idx in img_idx])
        trainval_ann_path.extend([os.path.join(voc_path, 'VOC2007', 'Annotations', idx + '.xml') for idx in img_idx])

        img_idx_path = os.path.join(voc_path, 'VOC2007', 'ImageSets', 'Main', 'test.txt')
        img_idx = _read_voc_txt(img_idx_path)
        test_img_path.extend([os.path.join(voc_path, 'VOC2007', 'JPEGImages', idx + '.jpg') for idx in img_idx])
        test_ann_path.extend([os.path.join(voc_path, 'VOC2007', 'Annotations', idx + '.xml') for idx in img_idx])

    if version == '12' or version == '07+12':
        img_idx_path = os.path.join(voc_path, 'VOC2012', 'ImageSets', 'Main', 'trainval.txt')
        img_idx = _read_voc_txt(img_idx_path)
        trainval_img_path.extend([os.path.join(voc_path, 'VOC2012', 'JPEGImages', idx + '.jpg') for idx in img_idx])
        trainval_ann_path.extend([os.path.join(voc_path, 'VOC2012', 'Annotations', idx + '.xml') for idx in img_idx])

        # we don't have test dataset of VOC2012
        # img_idx_path = os.path.join(voc_path, 'VOC2012', 'ImageSets', 'Main', 'test.txt')
        # img_idx = _read_voc_txt(img_idx_path)
        # test_img_path.extend([os.path.join(voc_path, 'VOC2012', 'JPEGImages', idx + '.jpg') for idx in img_idx])
        # test_ann_path.extend([os.path.join(voc_path, 'VOC2012', 'Annotations', idx + '.xml') for idx in img_idx])

    # voc_name_path = os.path.join('.', 'data', 'classes', 'voc.name')
    voc_name = _read_voc_txt(voc_name_path)
    trainval_txt_path = os.path.join(txt_output_path, 'trainval' + version + '.txt')
    test_txt_path = os.path.join(txt_output_path, 'test' + version + '.txt')

    def _check_bbox(sx1, sy1, sx2, sy2, sw, sh):
        x1, y1, x2, y2, w, h = int(sx1), int(sy1), int(sx2), int(sy2), int(sw), int(sh)

        if x1 < 1 or x2 < 1 or x1 > w or x2 > w or y1 < 1 or y2 < 1 or y1 > h or y2 > h:
            logging.warning('cross boundary (' + sw + ',' + sh + '),'.join([sx1, sy1, sx2, sy2]))

            return str(min(max(x1, 0), w)), str(min(max(y1, 0), h)), str(min(max(x2, 0), w)), str(min(max(y2, 0), h))

        return str(x1), str(y1), str(x2), str(y2)

    def _write_to_text(img_paths, ann_paths, txt_path):
        with open(txt_path, 'w') as f:
            for img_path, ann_path in zip(img_paths, ann_paths):
                root = ET.parse(ann_path).getroot()
                objects = root.findall('object')
                line = img_path

                size = root.find('size')
                width = size.find('width').text.strip()
                height = size.find('height').text.strip()

                for obj in objects:
                    difficult = obj.find('difficult').text.strip()
                    if (not use_difficult) and difficult == '1':
                        continue

                    bbox = obj.find('bndbox')
                    class_idx = voc_name.index(obj.find('name').text.lower().strip())
                    xmin = bbox.find('xmin').text.strip()
                    xmax = bbox.find('xmax').text.strip()
                    ymin = bbox.find('ymin').text.strip()
                    ymax = bbox.find('ymax').text.strip()

                    xmin, ymin, xmax, ymax = _check_bbox(xmin, ymin, xmax, ymax, width, height)

                    line += ' ' + ','.join([xmin, ymin, xmax, ymax, str(class_idx)])

                logging.info(line)
                f.write(line + '\n')

    _write_to_text(trainval_img_path, trainval_ann_path, trainval_txt_path)
    _write_to_text(test_img_path, test_ann_path, test_txt_path)

    return len(trainval_img_path), len(test_img_path)


def main(_argv):
    num_trainval, num_test = convert(FLAGS.voc_path, FLAGS.name_path, FLAGS.txt_output_path, FLAGS.version, FLAGS.use_difficult)
    logging.info("trainval: {}, test: {}".format(num_trainval, num_test))


if __name__ == '__main__':
    app.run(main)