import os
import re
import requests

def download_m3u(url, name):
    print(f"正在下载【{name}】的数据...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"下载【{name}】失败: {e}")
        return ""

def parse_m3u_content(content):
    """
    解析 m3u 文本，提取出 (info_line, url_line) 组成的元组集合
    """
    channels = set()
    lines = content.split('\n')
    current_info = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            current_info = line
        elif line.startswith("http://") or line.startswith("https://") or line.startswith("rtp://"):
            if current_info:
                channels.add((current_info, line))
                current_info = None  # 匹配完一组，重置
            else:
                # 如果没有 #EXTINF 头，单独的 URL 也可以作为无名频道保留
                channels.add(("#EXTINF:-1 ,未知频道", line))
    return channels

def main():
    output_file = "history_accumulated.m3u"
    all_channels = set()

    # 1. 如果本地已经有累积的历史文件，先读取进来，确保历史不丢失
    if os.path.exists(output_file):
        print(f"检测到本地历史文件 {output_file}，正在读取历史积累数据...")
        with open(output_file, 'r', encoding='utf-8') as f:
            all_channels.update(parse_m3u_content(f.read()))
        print(f"当前已载入历史历史频道数: {len(all_channels)} 个")

    # 2. 定义需要抓取的 3 个目标链接
    targets = {
        "咖啡": "https://iptv.catvod.com/kf/catvod.m3u",
        "OK": "https://iptv.catvod.com/ok/catvod.m3u",
        "88": "https://iptv.catvod.com/88/catvod.m3u"
    }

    # 3. 循环下载并合并去重
    for name, url in targets.items():
        content = download_m3u(url, name)
        if content:
            new_channels = parse_m3u_content(content)
            all_channels.update(new_channels)
            print(f"【{name}】本次获取到 {len(new_channels)} 个频道")

    # 4. 把累积去重后的所有渠道，重新写回到 m3u 文件中
    print(f"同步去重完成，全库当前总计累积有效频道数: {len(all_channels)} 个。开始写入文件...")
    
    # 按照频道名称或URL排序，让文件更加整洁
    sorted_channels = sorted(list(all_channels), key=lambda x: (x[0], x[1]))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for info, url in sorted_channels:
            f.write(f"{info}\n")
            f.write(f"{url}\n")
            
    print(f"数据成功累积并保存至 -> {output_file}")

if __name__ == "__main__":
    main()
