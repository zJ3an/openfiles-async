<div align="center">

# OpenFiles Async

An asynchronous version of the Python SDK for interacting with the Openfiles API

[![Support Me](https://img.shields.io/badge/Support%20Me-Donate-yellow?style=for-the-badge)](https://zj3an.vercel.app/donate.html)

</div>

## Usage

```python
import asyncio
from openfiles_async import AsyncOpenfilesClient

async def main():
    # Initialize the client
    async with AsyncOpenfilesClient(api_token="your_api_token") as client:
        
        # Get user information
        user_info = await client.get_user_info()
        print(f"User ID: {user_info.uid}")
        print(f"Space left: {user_info.space_left} / {user_info.capacity}")
        
        # List user files
        files = await client.get_user_files_list()
        print(f"Total files: {len(files)}")
        for file in files:
            print(f"File: {file.filename}, Size: {file.size}, Bag ID: {file.bag_id}")
        
        # Upload a file
        response = await client.upload_file(
            file_path="test/file.txt", 
            description="My file description"
        )
        file_bag_id = response.bag_id
        print(f"File uploaded with bag_id: {file_bag_id}")
        
        # Upload a folder (as ZIP)
        folder_response = await client.upload_folder(
            folder_path="test/folder", 
            description="My folder description"
        )
        print(f"Folder uploaded with bag_id: {folder_response.bag_id}")
        
        # Download a file
        downloaded_path = await client.download_file(
            bag_id=file_bag_id, 
            destination="test/downloaded_file.txt"
        )
        print(f"File downloaded to: {downloaded_path}")
        
        # Add file by bag ID
        await client.add_by_bag_id(bag_id=file_bag_id)
        print("File added by bag ID")
        
        # Delete a file
        await client.delete_file(bag_id=file_bag_id)
        print("File deleted")
        
        # Concurrent operations (run multiple operations at the same time)
        user_info, files_list = await asyncio.gather(
            client.get_user_info(),
            client.get_user_files_list()
        )
        print("Multiple operations completed simultaneously!")

# Run the example
asyncio.run(main())
```

## Features

- 📋 **List account files** - Get all files in your account
- 📤 **Upload files** - Upload individual files to TON storage
- 📁 **Upload folders** - Upload entire folders as ZIP files
- 📥 **Download files** - Download files by bag ID
- 🗑️ **Delete files** - Remove files from storage
- 👤 **Get user info** - Access account information and storage limits
- 🔗 **Add by bag ID** - Add existing files by their bag ID
- ⚡ **Concurrent operations** - Run multiple operations simultaneously
- 🔄 **Async/await support** - Fully asynchronous operations
- 🎯 **Context manager** - Automatic session management

## Requirements

- Python 3.8+
- aiohttp >= 3.8.0
- aiofiles >= 22.1.0  
- pydantic >= 1.10.0

## Installation

```bash
pip install aiohttp aiofiles pydantic
```

## License

MIT License
