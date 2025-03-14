document.addEventListener("DOMContentLoaded", () => {
  const addProductForm = document.getElementById("add-product-form");
  const productList = document.getElementById("product-list");
  const message = document.getElementById("add-product-message");

  // Fetch and display products
  async function loadProducts() {
    try {
      const response = await fetch("/admin/products");
      const result = await response.json();
      if (result.success) {
        productList.innerHTML = "";
        for (const [id, product] of Object.entries(result.products)) {
          const li = document.createElement("li");
          li.innerHTML = `
            ${product.name} - $${product.price} (Stock: ${product.stock})
            <img src="${product.image_url}" alt="${product.name}" width="100">
            <button onclick="removeProduct('${id}')">Remove</button>
          `;
          productList.appendChild(li);
        }
      }
    } catch (err) {
      console.error("Error loading products:", err);
    }
  }

  // Add product
  addProductForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("name").value;
    const price = document.getElementById("price").value;
    const stock = document.getElementById("stock").value;
    const imageFile = document.getElementById("image").files[0];

    const formData = new FormData();
    formData.append("name", name);
    formData.append("price", price);
    formData.append("stock", stock);
    formData.append("image", imageFile);

    try {
      const response = await fetch("/admin/add-product", {
        method: "POST",
        body: JSON.stringify({
          name: name,
          price: price,
          stock: stock,
          image_path: imageFile.name  // Send the file name as a placeholder
        }),
        headers: { "Content-Type": "application/json" }
      });

      const result = await response.json();
      if (result.success) {
        message.textContent = "Product added successfully!";
        message.style.color = "green";
        loadProducts(); // Refresh products list
      } else {
        throw new Error(result.message);
      }
    } catch (err) {
      message.textContent = `Error: ${err.message}`;
      message.style.color = "red";
    }
  });

  // Remove product
  window.removeProduct = async (id) => {
    try {
      const response = await fetch(`/admin/remove-product/${id}`, {
        method: "DELETE",
      });

      const result = await response.json();
      if (result.success) {
        loadProducts(); // Refresh products list
      } else {
        alert(result.message);
      }
    } catch (err) {
      console.error("Error removing product:", err);
    }
  };

  loadProducts(); // Initial load
});
