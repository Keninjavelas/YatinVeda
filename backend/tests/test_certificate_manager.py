"""
Test script for Certificate Manager functionality
"""

import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.certificate_manager import CertificateManager, CertificateProvider, CertificateState


async def test_certificate_manager():
    """Test certificate manager functionality"""
    print("🔐 Testing YatinVeda Certificate Manager")
    print("=" * 50)
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        cert_path = temp_path / "certs"
        key_path = temp_path / "keys"
        
        print(f"📁 Using temporary directory: {temp_dir}")
        
        # Test 1: Initialize Certificate Manager
        print("\n1. Initializing Certificate Manager...")
        try:
            manager = CertificateManager(
                cert_provider="self-signed",
                cert_path=str(cert_path),
                key_path=str(key_path),
                renewal_days=30,
                environment="development"
            )
            print("✅ Certificate Manager initialized successfully")
            print(f"   - Provider: {manager.cert_provider}")
            print(f"   - Environment: {manager.environment}")
            print(f"   - Certificate path: {manager.cert_path}")
            print(f"   - Key path: {manager.key_path}")
        except Exception as e:
            print(f"❌ Failed to initialize Certificate Manager: {e}")
            return False
        
        # Test 2: Provision self-signed certificate
        print("\n2. Provisioning self-signed certificate for localhost...")
        try:
            result = await manager.provision_certificate("localhost")
            if result.success:
                print("✅ Certificate provisioned successfully")
                print(f"   - Certificate: {result.certificate_path}")
                print(f"   - Private key: {result.private_key_path}")
                
                # Verify files exist
                if Path(result.certificate_path).exists() and Path(result.private_key_path).exists():
                    print("✅ Certificate files created successfully")
                else:
                    print("❌ Certificate files not found")
                    return False
            else:
                print(f"❌ Certificate provisioning failed: {result.error_message}")
                return False
        except Exception as e:
            print(f"❌ Exception during certificate provisioning: {e}")
            return False
        
        # Test 3: Validate certificate
        print("\n3. Validating certificate...")
        try:
            validation = await manager.validate_certificate("localhost")
            print(f"✅ Certificate validation completed")
            print(f"   - Valid: {validation.is_valid}")
            print(f"   - State: {validation.state}")
            print(f"   - Expiration: {validation.expiration_date}")
            print(f"   - Days until expiry: {validation.days_until_expiry}")
            
            if not validation.is_valid:
                print("❌ Certificate validation failed")
                return False
        except Exception as e:
            print(f"❌ Exception during certificate validation: {e}")
            return False
        
        # Test 4: Get certificate status
        print("\n4. Getting certificate status...")
        try:
            status = await manager.get_certificate_status("localhost")
            print("✅ Certificate status retrieved")
            print(f"   - Domain: {status.domain}")
            print(f"   - Status: {status.status}")
            print(f"   - Expires at: {status.expires_at}")
            print(f"   - Issuer: {status.issuer}")
        except Exception as e:
            print(f"❌ Exception getting certificate status: {e}")
            return False
        
        # Test 5: Check renewal needed
        print("\n5. Checking if renewal is needed...")
        try:
            domains_needing_renewal = await manager.check_renewal_needed()
            print(f"✅ Renewal check completed")
            print(f"   - Domains needing renewal: {domains_needing_renewal}")
        except Exception as e:
            print(f"❌ Exception during renewal check: {e}")
            return False
        
        # Test 6: Test invalid domain
        print("\n6. Testing invalid domain handling...")
        try:
            result = await manager.provision_certificate("invalid..domain")
            if not result.success:
                print("✅ Invalid domain correctly rejected")
                print(f"   - Error: {result.error_message}")
            else:
                print("❌ Invalid domain was accepted (should have been rejected)")
                return False
        except Exception as e:
            print(f"❌ Exception during invalid domain test: {e}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All Certificate Manager tests passed!")
        print("\nNext steps:")
        print("1. Install aiofiles: pip install aiofiles")
        print("2. For Let's Encrypt: Install certbot")
        print("3. For production: Configure domains and email")
        
        return True


async def test_configuration():
    """Test different configuration scenarios"""
    print("\n🔧 Testing Configuration Scenarios")
    print("=" * 50)
    
    # Test development configuration
    print("\n1. Testing development configuration...")
    dev_manager = CertificateManager(environment="development")
    print(f"✅ Development config: {dev_manager.config}")
    
    # Test staging configuration
    print("\n2. Testing staging configuration...")
    os.environ["STAGING_DOMAINS"] = "staging.example.com"
    staging_manager = CertificateManager(environment="staging")
    print(f"✅ Staging config: {staging_manager.config}")
    
    # Test production configuration
    print("\n3. Testing production configuration...")
    os.environ["PRODUCTION_DOMAINS"] = "example.com,api.example.com"
    prod_manager = CertificateManager(environment="production")
    print(f"✅ Production config: {prod_manager.config}")
    
    # Clean up environment variables
    os.environ.pop("STAGING_DOMAINS", None)
    os.environ.pop("PRODUCTION_DOMAINS", None)


def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking Dependencies")
    print("=" * 30)
    
    dependencies = {
        "aiofiles": "Required for async file operations",
        "openssl": "Required for certificate operations (system command)",
    }
    
    missing_deps = []
    
    # Check Python packages
    try:
        import aiofiles
        print("✅ aiofiles: Available")
    except ImportError:
        print("❌ aiofiles: Missing")
        missing_deps.append("aiofiles")
    
    # Check OpenSSL command
    try:
        import subprocess
        result = subprocess.run(["openssl", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ OpenSSL: {result.stdout.strip()}")
        else:
            print("❌ OpenSSL: Command failed")
            missing_deps.append("openssl")
    except FileNotFoundError:
        print("❌ OpenSSL: Not found in PATH")
        missing_deps.append("openssl")
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("\nInstallation instructions:")
        if "aiofiles" in missing_deps:
            print("  pip install aiofiles")
        if "openssl" in missing_deps:
            print("  Install OpenSSL for your system")
        return False
    else:
        print("\n✅ All dependencies available")
        return True


async def main():
    """Main test function"""
    print("🌌 YatinVeda Certificate Manager Test Suite")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Please install missing dependencies before running tests")
        return
    
    # Run configuration tests
    await test_configuration()
    
    # Run main functionality tests
    success = await test_certificate_manager()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("\nThe Certificate Manager is ready for use.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")


if __name__ == "__main__":
    asyncio.run(main())