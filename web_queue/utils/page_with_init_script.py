import playwright.async_api


async def page_with_init_script(
    page: playwright.async_api.Page,
) -> playwright.async_api.Page:
    await page.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'ja']});  # noqa: E501
        window.chrome = {runtime: {}};
    """
    )
    return page
