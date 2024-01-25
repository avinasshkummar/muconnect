document.addEventListener("DOMContentLoaded", function () {
  const bulkImportForm = document.getElementById("bulk-import-form");
  const addDataForm = document.getElementById("add-data-form");
  if (bulkImportForm) {
    bulkImportForm.addEventListener("submit", function (event) {
      event.preventDefault(); // Prevent the default form submission behavior

      // Handle the form submission here
      // Use AJAX to send the form data to the server and update the page dynamically
      const formData = new FormData(this);

      fetch("/bulk_import", {
        method: "POST",
        body: formData,
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Network response was not ok");
          }
          return response.json(); // or response.text() if the server returns plain text
        })
        .then((data) => {
          // Handle the response data here
          console.log(data);
          alert("Bulk import successful");
        })
        .catch((error) => {
          // Handle any errors here
          console.error(
            "There has been a problem with your fetch operation:",
            error
          );
        });
    });
  }
  if (addDataForm) {
    addDataForm.addEventListener("submit", async function (event) {
      event.preventDefault(); // Prevent the default form submission behavior

      // Get the form data
      const formData = new FormData(event.target);

      // Send the AJAX request

      try {
        const response = await fetch("/add_data", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Network response was not ok");
        }

        const data = await response.json(); // or response.text() if the server returns plain text

        // Handle the response data here
        console.log(data);
        alert("Data added successfully");
      } catch (error) {
        // Handle any errors here
        console.error(
          "There has been a problem with your fetch operation:",
          error
        );
      }
    });
  }
});
