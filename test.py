from dendrite import AsyncDendrite


async def send_email(to, subject, message):
    client = AsyncDendrite(auth="outlook.live.com")

    # Navigate
    await client.goto(
        "https://outlook.live.com/mail/0/", expected_page="An email inbox"
    )

    # Create new email and populate fields
    await client.click("The new email button")
    await client.fill("The recipient field", to)
    await client.press("Enter")
    await client.fill("The subject field", subject)
    await client.fill("The message field", message)

    # Send email
    await client.press("Enter", hold_cmd=True)


if __name__ == "__main__":
    import asyncio

    asyncio.run(send_email("charles@dendrite.systems", "Hello", "This is a test email"))
