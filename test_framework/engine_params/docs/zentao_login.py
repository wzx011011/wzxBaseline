import asyncio
import json
import random
from dotenv import load_dotenv
import os
from playwright.async_api import async_playwright

# 定义空的stealth函数（禅道不需要隐藏自动化特征）
async def stealth_async(page):
    pass

# 加载.env中的账号信息
load_dotenv()

# 禅道配置
ZENTAO_BASE_URL = os.getenv("ZENTAO_URL")
USERNAME = os.getenv("ZENTAO_USERNAME")
PASSWORD = os.getenv("ZENTAO_PASSWORD")
TARGET_BUG_URL = os.getenv("TARGET_BUG_URL")
COOKIE_FILE = "zentao_cookies.json"


async def zentao_auto_login():
    """禅道自动登录并获取Bug页面内容"""
    async with async_playwright() as p:
        # 1. 启动Chrome浏览器（非无头模式）
        browser = await p.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )
        context = await browser.new_context(
            viewport=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # 2. 隐藏自动化特征
        await stealth_async(page)

        try:
            print(f"📡 正在访问目标页面: {TARGET_BUG_URL}")
            # 3. 访问目标bug页面
            await page.goto(TARGET_BUG_URL)
            await page.wait_for_load_state("networkidle")

            # 4. 检查是否需要登录
            if "user-login" in page.url:
                print("🔐 检测到登录页面，开始自动登录...")
                
                # 输入用户名
                await page.locator("#account").click()
                await page.locator("#account").fill("")  # 先清空
                await page.locator("#account").type(USERNAME, delay=random.randint(80, 150))
                
                # 输入密码
                await page.locator("#password").click()
                await page.locator("#password").fill("")
                await page.locator("#password").type(PASSWORD, delay=random.randint(80, 150))
                
                # 点击登录按钮
                print("👉 点击登录按钮...")
                await page.locator("#submit").click()
                await page.wait_for_load_state("networkidle")
                
                # 等待可能的跳转
                await asyncio.sleep(2)

            # 5. 验证登录状态
            current_url = page.url
            if "user-login" in current_url:
                print("❌ 登录失败，请检查账号密码")
                await page.screenshot(path="login_failed.png")
                return None
            
            print("✅ 登录成功！")
            
            # 6. 保存Cookie
            cookies = await context.cookies()
            with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print(f"🍪 Cookie已保存到 {COOKIE_FILE}")
            
            # 7. 如果不在目标Bug页面，跳转过去
            if TARGET_BUG_URL not in current_url:
                print(f"🔄 跳转到目标Bug页面...")
                await page.goto(TARGET_BUG_URL)
                await page.wait_for_load_state("networkidle")
            
            # 8. 提取Bug页面内容
            print("📄 正在提取Bug页面内容...")
            
            # 等待页面完全加载
            await asyncio.sleep(2)
            
            # 截图保存
            await page.screenshot(path="bug_page_screenshot.png", full_page=True)
            print("📸 页面截图已保存到 bug_page_screenshot.png")
            
            # 提取页面文本内容
            content = await page.content()
            with open("bug_page_content.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("💾 页面HTML已保存到 bug_page_content.html")
            
            # 尝试提取Bug的关键信息
            try:
                bug_info = {}
                
                # 尝试多种选择器定位Bug信息
                selectors = {
                    "title": ["h1", ".page-title", "#bugTitle", ".bug-title"],
                    "description": [".bug-content", ".article-content", "#bugSteps"],
                    "status": [".bug-status", "[data-field='status']"],
                }
                
                for field, selector_list in selectors.items():
                    for selector in selector_list:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                text = await element.inner_text()
                                if text and text.strip():
                                    bug_info[field] = text.strip()
                                    break
                        except:
                            continue
                
                if bug_info:
                    print("\n📋 提取到的Bug信息:")
                    for key, value in bug_info.items():
                        print(f"  {key}: {value[:100]}..." if len(value) > 100 else f"  {key}: {value}")
                    
                    with open("bug_info.json", "w", encoding="utf-8") as f:
                        json.dump(bug_info, f, indent=2, ensure_ascii=False)
                    print("💾 Bug信息已保存到 bug_info.json")
                
            except Exception as e:
                print(f"⚠️  提取Bug信息时出错: {str(e)}")
            
            print("\n✨ 完成！浏览器窗口将保持打开，您可以手动查看页面内容")
            print("按 Ctrl+C 可关闭浏览器")
            
            # 保持浏览器打开
            await asyncio.sleep(300)  # 保持5分钟
            
        except KeyboardInterrupt:
            print("\n👋 用户中断，正在关闭浏览器...")
        except Exception as e:
            print(f"❌ 操作出错：{str(e)}")
            await page.screenshot(path="error_screenshot.png")
        finally:
            await browser.close()


async def load_cookies_and_visit():
    """使用已保存的Cookie直接访问（无需重新登录）"""
    if not os.path.exists(COOKIE_FILE):
        print("❌ 未找到Cookie文件，请先运行登录流程")
        return
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(viewport=None)
        
        # 加载Cookie
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        await stealth_async(page)
        
        print(f"🍪 使用已保存的Cookie访问: {TARGET_BUG_URL}")
        await page.goto(TARGET_BUG_URL)
        await page.wait_for_load_state("networkidle")
        
        if "user-login" in page.url:
            print("❌ Cookie已失效，请重新登录")
            await browser.close()
            return
        
        print("✅ 访问成功！")
        await page.screenshot(path="bug_page_screenshot.png", full_page=True)
        
        await asyncio.sleep(60)
        await browser.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--use-cookie":
        print("🍪 使用Cookie模式")
        asyncio.run(load_cookies_and_visit())
    else:
        print("🔐 完整登录模式")
        asyncio.run(zentao_auto_login())
