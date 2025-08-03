"""
Simple test to demonstrate the usage of the Openfiles async SDK
"""

import asyncio
import os
from pathlib import Path
import tempfile
from openfiles_async import AsyncOpenfilesClient


async def test_basic_usage():
    """
    Basic test showing all main functions
    """
    print("🚀 Starting Openfiles async SDK test")
    print("=" * 50)
    
    # Check if we have the API token
    if not os.environ.get("OPENFILES_API_TOKEN"):
        print("⚠️  IMPORTANT: Set the OPENFILES_API_TOKEN variable")
        print("   Example: set OPENFILES_API_TOKEN=your_token_here")
        print("   Or use: AsyncOpenfilesClient(api_token='your_token')")
        return
    
    async with AsyncOpenfilesClient() as client:
        try:
            # 1. Get user information
            print("1️⃣  Getting user information...")
            user_info = await client.get_user_info()
            print(f"   ✅ User ID: {user_info.uid}")
            print(f"   ✅ Space left: {user_info.space_left:.2f} MB")
            print(f"   ✅ Total capacity: {user_info.capacity:.2f} MB")
            print()
            
            # 2. List user files
            print("2️⃣  Getting file list...")
            files = await client.get_user_files_list()
            print(f"   ✅ Total files: {len(files)}")
            
            if files:
                print("   📁 First 3 files:")
                for i, file in enumerate(files[:3], 1):
                    print(f"      {i}. {file.filename} ({file.size} bytes)")
                    print(f"         Bag ID: {file.bag_id}")
                    print(f"         Description: {file.description}")
            else:
                print("   📭 No files in account")
            print()
            
            # 3. Create test file and upload it
            print("3️⃣  Creating and uploading test file...")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write("Hello from the Openfiles async SDK!\n")
                temp_file.write(f"File created at: {asyncio.get_event_loop().time()}\n")
                temp_file.write("This is a test file.")
                temp_path = Path(temp_file.name)
            
            try:
                # Upload file
                upload_response = await client.upload_file(
                    file_path=temp_path,
                    description="Test file from async SDK"
                )
                bag_id = upload_response.bag_id
                print(f"   ✅ File uploaded successfully!")
                print(f"   ✅ Bag ID: {bag_id}")
                print()
                
                # 4. Download the file we just uploaded
                print("4️⃣  Downloading file...")
                download_path = temp_path.parent / f"downloaded_{temp_path.name}"
                
                result = await client.download_file(
                    bag_id=bag_id,
                    destination=download_path
                )
                print(f"   ✅ File downloaded to: {result}")
                
                # Verify content
                if Path(result).exists():
                    with open(result, 'r') as f:
                        content = f.read()
                    print(f"   ✅ Content verified: {len(content)} characters")
                print()
                
                # 5. Delete the file
                print("5️⃣  Deleting test file...")
                await client.delete_file(bag_id=bag_id)
                print(f"   ✅ File {bag_id} deleted successfully")
                print()
                
            finally:
                # Clean up temporary files
                if temp_path.exists():
                    temp_path.unlink()
                if download_path.exists():
                    download_path.unlink()
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            print(f"   Error type: {type(e).__name__}")


async def test_concurrent_operations():
    """
    Test demonstrating concurrent operations - the key advantage of the async SDK
    """
    print("⚡ Demonstrating concurrent operations")
    print("=" * 50)
    
    if not os.environ.get("OPENFILES_API_TOKEN"):
        print("⚠️  You need to configure OPENFILES_API_TOKEN")
        return
    
    async with AsyncOpenfilesClient() as client:
        try:
            print("🔄 Running multiple operations simultaneously...")
            
            # Execute operations concurrently
            start_time = asyncio.get_event_loop().time()
            
            user_info, files_list = await asyncio.gather(
                client.get_user_info(),
                client.get_user_files_list()
            )
            
            end_time = asyncio.get_event_loop().time()
            
            print(f"   ✅ Operations completed in {end_time - start_time:.2f} seconds")
            print(f"   ✅ User: {user_info.uid}")
            print(f"   ✅ Files retrieved: {len(files_list)}")
            print("   💡 Both operations ran simultaneously!")
            print()
            
        except Exception as e:
            print(f"❌ Error in concurrent operations: {e}")


async def test_folder_upload():
    """
    Test folder upload (as ZIP)
    """
    print("📁 Folder upload test")
    print("=" * 50)
    
    if not os.environ.get("OPENFILES_API_TOKEN"):
        print("⚠️  You need to configure OPENFILES_API_TOKEN")
        return
    
    # Create temporary folder with files
    with tempfile.TemporaryDirectory() as temp_dir:
        folder_path = Path(temp_dir) / "test_folder"
        folder_path.mkdir()
        
        # Create some files in the folder
        (folder_path / "file1.txt").write_text("Content of file 1")
        (folder_path / "file2.txt").write_text("Content of file 2")
        (folder_path / "readme.md").write_text("# Test Folder\nThis is a test folder.")
        
        print(f"📂 Folder created with {len(list(folder_path.iterdir()))} files")
        
        async with AsyncOpenfilesClient() as client:
            try:
                print("📤 Uploading folder...")
                
                response = await client.upload_folder(
                    folder_path=folder_path,
                    description="Test folder from async SDK"
                )
                
                print(f"   ✅ Folder uploaded successfully!")
                print(f"   ✅ Bag ID: {response.bag_id}")
                print()
                
                # Delete the uploaded folder
                print("🗑️  Deleting folder...")
                await client.delete_file(bag_id=response.bag_id)
                print("   ✅ Folder deleted successfully")
                
            except Exception as e:
                print(f"❌ Error uploading folder: {e}")


async def test_add_by_bag_id():
    """
    Test add file by bag ID
    """
    print("🔗 Add by Bag ID test")
    print("=" * 50)
    
    if not os.environ.get("OPENFILES_API_TOKEN"):
        print("⚠️  You need to configure OPENFILES_API_TOKEN")
        return
    
    async with AsyncOpenfilesClient() as client:
        try:
            # First get file list to find a valid bag_id
            files = await client.get_user_files_list()
            
            if not files:
                print("📭 No files in account to test this function")
                print("   💡 Upload a file first to test add_by_bag_id")
                return
            
            # Use the first file as example
            test_bag_id = files[0].bag_id
            print(f"🎯 Testing with bag_id: {test_bag_id}")
            print(f"   📄 File: {files[0].filename}")
            
            await client.add_by_bag_id(bag_id=test_bag_id)
            print("   ✅ add_by_bag_id executed successfully")
            
        except Exception as e:
            print(f"❌ Error in add_by_bag_id: {e}")


def print_header():
    """Print test header"""
    print()
    print("🧪 OPENFILES ASYNC SDK - TESTS")
    print("=" * 60)
    print("This script demonstrates all SDK functionalities")
    print("=" * 60)
    print()


async def main():
    """Main function that runs all tests"""
    print_header()
    
    # Run tests sequentially
    await test_basic_usage()
    await test_concurrent_operations() 
    await test_folder_upload()
    await test_add_by_bag_id()
    
    print("🎉 All tests completed!")
    print("=" * 60)
    print("💡 Tips:")
    print("   • Always use 'async with AsyncOpenfilesClient() as client:'")
    print("   • Use asyncio.gather() for concurrent operations")
    print("   • Handle errors with try/except like in synchronous code")
    print("   • The async SDK is especially useful for multiple operations")


if __name__ == "__main__":
    # Run the main test
    asyncio.run(main())
