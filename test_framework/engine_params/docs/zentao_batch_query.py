"""
禅道Bug批量查询工具
从禅道系统批量获取Bug详细信息
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
from datetime import datetime
import aiohttp

# 加载环境变量
load_dotenv()

ZENTAO_URL = os.getenv('ZENTAO_URL', 'https://zentao.creality.com/zentao')
USERNAME = os.getenv('ZENTAO_USERNAME')
PASSWORD = os.getenv('ZENTAO_PASSWORD')
COOKIE_FILE = "zentao_cookies.json"

# Bug ID列表
BUG_IDS = [
    10735, 10736, 10737, 10738, 10753, 10754, 10755,
    11182, 11183, 11184, 11185, 11187, 11188, 11189, 11190, 11192, 11193, 11194,
    11272, 11279, 11280, 11320, 11327, 11329, 11339, 11340,
    11456, 11457, 11459, 11460, 11461, 11462, 11463, 11464, 11467, 11471, 11473,
    13275, 13276, 13277, 13278, 13279, 13282, 13283, 13285,
    13303, 13309, 13334, 13344, 13346, 13349, 13352, 13364, 13366, 13375, 13377, 13379, 13381, 13384, 13395,
    13496, 13511, 13533, 13534, 13537, 13555, 13570,
    13607, 13608, 13621, 13624, 13647, 13653, 13655, 13704,
    13813, 13826, 13851
]

async def login(page):
    """登录禅道"""
    print(f"\n🔐 登录禅道: {ZENTAO_URL}")
    
    await page.goto(f"{ZENTAO_URL}/bug-browse-19.html", timeout=30000)
    await asyncio.sleep(2)
    
    try:
        # 尝试多种选择器
        account_selectors = ['#account', 'input[name="account"]', 'input[placeholder*="账"]', 'input[type="text"]']
        password_selectors = ['[name="password"]', 'input[type="password"]', '#password']
        
        # 填写账号
        for selector in account_selectors:
            try:
                await page.fill(selector, USERNAME, timeout=5000)
                print(f"✓ 使用选择器填写账号: {selector}")
                break
            except:
                continue
        
        # 填写密码
        for selector in password_selectors:
            try:
                await page.fill(selector, PASSWORD, timeout=5000)
                print(f"✓ 使用选择器填写密码: {selector}")
                break
            except:
                continue
        
        # 点击登录按钮
        submit_selectors = ['#submit', 'button[type="submit"]', '[type="submit"]', 'button:has-text("登录")']
        for selector in submit_selectors:
            try:
                await page.click(selector, timeout=5000)
                print(f"✓ 点击登录按钮: {selector}")
                break
            except:
                continue
        
        # 等待登录成功
        await page.wait_for_url(lambda url: 'user-login' not in url, timeout=10000)
        print("✓ 登录成功")
        
    except Exception as e:
        print(f"⚠ 自动登录失败: {e}")
        print("请在浏览器中手动登录，然后按Enter继续...")
        input()
        print("✓ 手动登录完成")

async def get_bug_info(page, bug_id, context, download_images=True):
    """获取单个Bug的详细信息"""
    bug_url = f"{ZENTAO_URL}/bug-view-{bug_id}.html"
    
    try:
        await page.goto(bug_url, timeout=15000)
        await asyncio.sleep(3)  # 等待iframe加载
        
        # 等待并切换到iframe (Bug内容在 app-qa iframe中)
        try:
            frame = page.frame(name="app-qa")
            if not frame:
                # 再等待一下iframe加载
                await asyncio.sleep(2)
                frame = page.frame(name="app-qa")
            
            if not frame:
                # 如果还没有，直接在主页面提取
                frame = page
            else:
                # 等待iframe内容加载
                await asyncio.sleep(2)
        except:
            frame = page
        
        # 提取Bug信息和图片链接
        bug_info = await frame.evaluate("""
            () => {
                const getText = (selector) => {
                    const el = document.querySelector(selector);
                    return el ? el.textContent.trim() : '';
                };
                
                const getTableValue = (label) => {
                    const cells = Array.from(document.querySelectorAll('td, th'));
                    for (let i = 0; i < cells.length; i++) {
                        if (cells[i].textContent.includes(label) && cells[i+1]) {
                            return cells[i+1].textContent.trim();
                        }
                    }
                    return '';
                };
                
                // 提取重现步骤的完整HTML内容
                let stepsHtml = '';
                let stepsText = '';
                
                // 方法1: 查找包含"重现步骤"文本的元素，然后找它后面的内容
                const allElements = Array.from(document.querySelectorAll('*'));
                let stepsEl = null;
                
                for (const el of allElements) {
                    const text = el.textContent || '';
                    // 如果元素文本正好是"重现步骤"（不是整个页面都包含）
                    if (text.trim() === '重现步骤' || text.trim() === 'Steps') {
                        // 找下一个兄弟元素
                        let nextEl = el.nextElementSibling;
                        if (nextEl) {
                            stepsEl = nextEl;
                            break;
                        }
                        // 或者找父元素的下一个兄弟
                        nextEl = el.parentElement?.nextElementSibling;
                        if (nextEl) {
                            stepsEl = nextEl;
                            break;
                        }
                    }
                }
                
                // 方法2: 使用data-name属性
                if (!stepsEl) {
                    const selectors = [
                        '[data-name="steps"]',
                        'td[data-name="steps"]',
                        '.steps',
                        '#steps'
                    ];
                    
                    for (const selector of selectors) {
                        stepsEl = document.querySelector(selector);
                        if (stepsEl) break;
                    }
                }
                
                // 方法3: 查找所有td，看前一个是否是"重现步骤"
                if (!stepsEl) {
                    const allTds = Array.from(document.querySelectorAll('td'));
                    for (const td of allTds) {
                        const prev = td.previousElementSibling;
                        if (prev && (prev.textContent.includes('重现步骤') || prev.textContent.includes('Steps'))) {
                            stepsEl = td;
                            break;
                        }
                    }
                }
                
                if (stepsEl) {
                    stepsHtml = stepsEl.innerHTML;
                    stepsText = stepsEl.textContent.trim();
                }
                
                // 从重现步骤中提取所有图片
                const images = [];
                if (stepsEl) {
                    stepsEl.querySelectorAll('img').forEach(img => {
                        images.push({
                            src: img.src,
                            alt: img.alt || '',
                            title: img.title || ''
                        });
                    });
                }
                
                // 如果重现步骤中没找到图片，搜索整个页面的file-read图片
                if (images.length === 0) {
                    document.querySelectorAll('img').forEach(img => {
                        if (img.src && img.src.includes('file-read')) {
                            images.push({
                                src: img.src,
                                alt: img.alt || '',
                                title: img.title || ''
                            });
                        }
                    });
                }
                
                return {
                    title: getText('h2, .page-title, [class*="title"]') || document.title.split('-')[0].trim(),
                    status: getTableValue('状态') || getTableValue('status'),
                    severity: getTableValue('严重程度') || getTableValue('severity'),
                    priority: getTableValue('优先级') || getTableValue('priority'),
                    assignedTo: getTableValue('指派给') || getTableValue('assignedTo'),
                    createdBy: getTableValue('由谁创建') || getTableValue('openedBy'),
                    createdDate: getTableValue('创建日期') || getTableValue('openedDate'),
                    resolvedBy: getTableValue('解决者') || getTableValue('resolvedBy'),
                    resolution: getTableValue('解决方案') || getTableValue('resolution'),
                    steps: stepsText,
                    stepsHtml: stepsHtml,
                    images: images
                };
            }
        """)
        
        bug_info['id'] = bug_id
        bug_info['url'] = bug_url
        
        # 使用aiohttp通过cookies下载图片
        if download_images and bug_info.get('images'):
            import aiohttp
            from pathlib import Path
            
            images_dir = Path(f"zentao_images/bug_{bug_id}")
            images_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取cookies
            cookies_list = await context.cookies()
            cookies_dict = {c['name']: c['value'] for c in cookies_list}
            
            downloaded_images = []
            failed_count = 0
            
            async with aiohttp.ClientSession(cookies=cookies_dict) as session:
                for idx, img in enumerate(bug_info['images'], 1):
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Referer': bug_url
                        }
                        
                        async with session.get(img['src'], headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                            if resp.status == 200:
                                content = await resp.read()
                                
                                # 从URL或content-type确定文件扩展名
                                content_type = resp.headers.get('content-type', '')
                                if 'jpeg' in content_type or 'jpg' in content_type:
                                    ext = 'jpg'
                                elif 'png' in content_type:
                                    ext = 'png'
                                elif 'gif' in content_type:
                                    ext = 'gif'
                                else:
                                    # 从URL提取
                                    ext = img['src'].split('.')[-1].split('?')[0].lower()
                                    if ext not in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                                        ext = 'jpg'
                                
                                img_path = images_dir / f"image_{idx}.{ext}"
                                img_path.write_bytes(content)
                                downloaded_images.append(str(img_path))
                            else:
                                failed_count += 1
                                error_log = images_dir / "download_errors.txt"
                                with open(error_log, 'a', encoding='utf-8') as f:
                                    f.write(f"图片 {idx} HTTP状态码: {resp.status}\n")
                                    f.write(f"  URL: {img['src']}\n\n")
                                    
                    except Exception as e:
                        failed_count += 1
                        error_log = images_dir / "download_errors.txt"
                        with open(error_log, 'a', encoding='utf-8') as f:
                            f.write(f"图片 {idx} 下载失败: {e}\n")
                            f.write(f"  URL: {img['src']}\n\n")
            
            bug_info['downloaded_images'] = downloaded_images
            if downloaded_images:
                print(f"  ✓ Bug {bug_id}: {bug_info['title'][:50]}... (成功 {len(downloaded_images)} 张，失败 {failed_count} 张)")
            else:
                img_count = len(bug_info.get('images', []))
                if img_count > 0:
                    print(f"  ✓ Bug {bug_id}: {bug_info['title'][:50]}... (发现 {img_count} 张图片但全部下载失败)")
                else:
                    print(f"  ✓ Bug {bug_id}: {bug_info['title'][:50]}...")
        else:
            print(f"  ✓ Bug {bug_id}: {bug_info['title'][:50]}...")
        
        return bug_info
        
    except Exception as e:
        print(f"  ✗ Bug {bug_id}: 获取失败 - {e}")
        return {
            'id': bug_id,
            'url': bug_url,
            'error': str(e),
            'title': '',
            'status': '',
            'severity': '',
            'priority': '',
            'assignedTo': '',
            'createdBy': '',
            'createdDate': '',
            'resolvedBy': '',
            'resolution': '',
            'steps': '',
            'stepsHtml': '',
            'images': [],
            'downloaded_images': []
        }

async def batch_query_bugs():
    """批量查询Bug信息"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # 尝试加载cookies
        cookie_path = Path(COOKIE_FILE)
        if cookie_path.exists():
            try:
                cookies = json.loads(cookie_path.read_text(encoding='utf-8'))
                await context.add_cookies(cookies)
                print(f"✓ 已加载 {len(cookies)} 个cookies")
            except:
                print("⚠ Cookie加载失败，将重新登录")
        
        page = await context.new_page()
        
        # 登录
        await login(page)
        
        # 保存新的cookies
        new_cookies = await context.cookies()
        with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_cookies, f, ensure_ascii=False, indent=2)
        print(f"✓ 已保存cookies")
        
        # 批量查询Bug
        print(f"\n📋 开始查询 {len(BUG_IDS)} 个Bug的详细信息...")
        print("="*80)
        
        all_bugs = []
        for i, bug_id in enumerate(BUG_IDS, 1):
            print(f"[{i}/{len(BUG_IDS)}]", end=" ")
            bug_info = await get_bug_info(page, bug_id, context)
            all_bugs.append(bug_info)
            await asyncio.sleep(0.5)  # 避免请求过快
        
        # 为每个Bug保存重现步骤HTML到单独文件
        for bug in all_bugs:
            if bug.get('stepsHtml'):
                steps_html_file = f"zentao_images/bug_{bug['id']}/steps.html"
                Path(steps_html_file).parent.mkdir(parents=True, exist_ok=True)
                with open(steps_html_file, 'w', encoding='utf-8') as hf:
                    hf.write(bug['stepsHtml'])
                bug['stepsHtmlFile'] = steps_html_file
        
        # 保存为JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f"zentao_bugs_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'query_time': datetime.now().isoformat(),
                'total_bugs': len(all_bugs),
                'bugs': all_bugs
            }, f, ensure_ascii=False, indent=2)
        print(f"\n💾 数据已保存到: {json_file}")
        
        # 统计信息
        success_count = sum(1 for bug in all_bugs if not bug.get('error'))
        error_count = len(all_bugs) - success_count
        total_images = sum(len(bug.get('downloaded_images', [])) for bug in all_bugs)
        
        print("\n" + "="*80)
        print("查询完成统计：")
        print("="*80)
        print(f"  总计: {len(all_bugs)} 个Bug")
        print(f"  成功: {success_count} 个")
        print(f"  失败: {error_count} 个")
        print(f"  图片: {total_images} 张")
        
        if error_count > 0:
            print("\n失败的Bug ID:")
            for bug in all_bugs:
                if bug.get('error'):
                    print(f"  - Bug {bug['id']}: {bug['error']}")
        
        print("\n⏳ 浏览器将在5秒后关闭...")
        await asyncio.sleep(5)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(batch_query_bugs())
