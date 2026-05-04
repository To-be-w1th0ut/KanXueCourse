from __future__ import annotations

from collections import defaultdict

GROUP_ORDER = [
    '公开可访问上传',
    'MIME / 扩展名信任',
    '文件名 / 路径控制',
]

LABS = [
    {
        'domain': 'upload',
        'slug': 'public-html',
        'title': 'L01 公开可访问 HTML 上传',
        'subtitle': '上传后的文件能被同源直接访问，浏览器会按内容执行。',
        'difficulty': '基础',
        'story': '课堂素材区允许学员上传“预览页面”。',
        'endpoint': '/labs/upload/public-html',
        'primary_class': '公开可访问上传',
        'secondary_class': '同源 HTML / SVG 执行',
        'timing_class': '上传后访问触发',
        'defense_focus': '限制类型 + 非同源存储 / 强制下载',
        'teacher_path': '先讲“文件上传不等于代码执行”，但只要同源可访问的 HTML/SVG 就会进入浏览器执行链。',
        'hints': [
            '先看上传后的文件是不是会在同源路径下直接打开。',
            '如果浏览器把它当 HTML/SVG 解析，文件本身就成了新的页面。',
            '安全模式应阻止危险类型，或至少强制附件下载。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh upload-public 重置上传文件。',
    },
    {
        'domain': 'upload',
        'slug': 'mime-trust',
        'title': 'L02 只信任 Content-Type',
        'subtitle': '如果服务器把用户声明的 MIME 直接当真，返回头本身就会放大风险。',
        'difficulty': '进阶',
        'story': '素材直传接口允许客户端声明 MIME，用于后续原样回放。',
        'endpoint': '/labs/upload/mime-trust',
        'primary_class': 'MIME / 扩展名信任',
        'secondary_class': '用户可控 Content-Type',
        'timing_class': '上传后访问触发',
        'defense_focus': '服务端决定响应类型，不信任客户端 MIME',
        'teacher_path': '这关适合讲“不是只有文件内容危险，响应头也决定浏览器如何解释”。',
        'hints': [
            '看服务端返回文件时，Content-Type 是怎么来的。',
            '如果类型完全由上传者声明，浏览器就会按那个类型解释。',
            '安全模式要由服务端重新判定或降级为下载。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh upload-public 重置上传文件。',
    },
    {
        'domain': 'upload',
        'slug': 'filename-traversal',
        'title': 'L03 文件名路径穿越与覆盖',
        'subtitle': '文件上传不只影响“内容”，文件名本身也可能改写写入位置。',
        'difficulty': '高级',
        'story': '公告横幅会读取 data 目录中的固定文件，而上传器直接使用用户文件名拼路径。',
        'endpoint': '/labs/upload/filename-traversal',
        'primary_class': '文件名 / 路径控制',
        'secondary_class': '路径穿越 / 覆盖现有文件',
        'timing_class': '上传后立即影响',
        'defense_focus': 'basename / 随机文件名 / 固定目录',
        'teacher_path': '把“文件内容安全”扩展到“文件名安全”，帮助学生建立完整上传面思维。',
        'hints': [
            '先观察服务端如何拼接目标路径。',
            '如果文件名能包含目录分隔符，可能就不再写入预期目录。',
            '安全模式要丢弃原文件名中的路径信息，并改用随机存储名。',
        ],
        'reset': '使用 ./scripts/reset_lab.sh upload 重置上传文件和横幅。',
    },
]

LAB_INDEX = {item['slug']: item for item in LABS}

def get_lab(slug: str):
    return LAB_INDEX[slug]

def build_taxonomy():
    grouped = defaultdict(list)
    for item in LABS:
        grouped[item['primary_class']].append(item)
    return [{'name': name, 'labs': grouped[name]} for name in GROUP_ORDER if grouped[name]]
