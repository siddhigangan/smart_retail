import os
from abc import ABC, abstractmethod

class BaseInvoiceStorage(ABC):
    @abstractmethod
    def save_invoice(self, filename: str, pdf_bytes: bytes) -> str:
        """
        Saves the generated invoice PDF and returns its public URL/URI.
        """
        pass

class LocalInvoiceStorage(BaseInvoiceStorage):
    def __init__(self, base_dir: str = "app/static/invoices", url_prefix: str = "/static/invoices"):
        self.base_dir = base_dir
        self.url_prefix = url_prefix
        # Ensure directories exist
        os.makedirs(self.base_dir, exist_ok=True)

    def save_invoice(self, filename: str, pdf_bytes: bytes) -> str:
        file_path = os.path.join(self.base_dir, filename)
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
        
        # Return URL
        return f"{self.url_prefix}/{filename}"

# Defaulting to LocalInvoiceStorage for local development.
# In the future, this can be swapped with S3InvoiceStorage or CloudinaryStorage
# by changing the instantiation here.
InvoiceStorageService = LocalInvoiceStorage()
