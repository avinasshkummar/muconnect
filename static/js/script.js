document.addEventListener("DOMContentLoaded", function () {
  const bulkImportForm = document.getElementById("bulk-import-form");
  const addDataForm = document.getElementById("add-data-form");
  const getDataForm = document.getElementById("filter-form");
  const loader = document.getElementById("loader");
  const overlay = document.getElementById("overlay");
  if (bulkImportForm) {
    bulkImportForm.addEventListener("submit",async function (event) {
      event.preventDefault(); // Prevent the default form submission behavior

      // Get the form data
      const formData = new FormData(event.target);
      // Send the AJAX request
      try {
        // Show loader
        loader.style.display = "block";
        overlay.style.display = "block";
        const response = await fetch("/bulk_import", {
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
      } finally {
        // Hide loader
        loader.style.display = "none";
        overlay.style.display = "none";
      }
    });
  }
  if (addDataForm) {
    addDataForm.addEventListener("submit", async function (event) {
      event.preventDefault(); // Prevent the default form submission behavior

      // Get the form data
      const formData = new FormData(event.target);

      // Send the AJAX request

      try {
        // Show loader
        loader.style.display = "block";
        overlay.style.display = "block";
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
      } finally {
        // Hide loader
        loader.style.display = "none";
        overlay.style.display = "none";
      }
    });
  }
  if (getDataForm) {
    getDataForm.addEventListener("submit", async function (event) {
      event.preventDefault(); // Prevent the default form submission behavior

      // Get the form data
      const formData = new FormData(event.target);

      // Send the AJAX request

      try {
        // Show loader
        loader.style.display = "block";
        overlay.style.display = "block";
        const response = await fetch("/get_data", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Network response was not ok");
        }

        const data = await response.json(); // or response.text() if the server returns plain text
        const tableData = data.data;
        let table = document.getElementById("data-table");

        // Clear the table
        table.innerHTML = "";

        // Create table header
        let thead = document.createElement("thead");
        let headerRow = document.createElement("tr");
        [
          ["applicant_id", "ID"],
          ["name", "Name"],
          ["number", "Phone Number"],
        ].forEach(([key, header]) => {
          let th = document.createElement("th");
          th.textContent = header;
          headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create table body
        let tbody = document.createElement("tbody");
        tableData.forEach((item) => {
          let row = document.createElement("tr");
          [
            ["applicant_id", "ID"],
            ["name", "Name"],
            ["number", "Phone Number"],
          ].forEach(([key, header]) => {
            let td = document.createElement("td");
            if (key === "applicant_id") {
              // Create a hyperlink for the applicant_id
              let a = document.createElement("a");
              a.href = "/profile/" + item[key]; // Replace with the actual path
              a.textContent = item[key];
              td.appendChild(a);
            } else {
              td.textContent = item[key];
            }
            row.appendChild(td);
          });
          tbody.appendChild(row);
        });
        table.appendChild(tbody);
      } catch (error) {
        // Handle any errors here
        console.error(
          "There has been a problem with your fetch operation:",
          error
        );
      } finally {
        // Hide loader
        loader.style.display = "none";
        overlay.style.display = "none";
      }
    });
  }
});
