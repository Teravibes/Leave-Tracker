document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables for DOM elements
    const prevMonthBtn = document.getElementById("prevMonth");
    const nextMonthBtn = document.getElementById("nextMonth");
    const monthYear = document.getElementById("monthYear");
    const calendarBody = document.getElementById("calendarBody");
    const clearSelectionBtn = document.getElementById("clearSelection");
    const dateCounter = document.getElementById("dateCounter");
    let selectedRange = { start: null, end: null };
  
  function getAllBusinessDatesInRange(start, end) {
    const dates = [];
    let current = new Date(start);

    while (current <= end) {
      const day = current.getDay();
      const isWeekend = day === 0 || day === 6;

      // Try to find the cell for this date in the current DOM
      const dateStr = current.toISOString().split("T")[0];
      const cell = calendarBody.querySelector(`td[data-date^="${dateStr}"]`);
      const isPublicHoliday = cell?.classList.contains("public-holiday");

      if (!isWeekend && !isPublicHoliday) {
        dates.push(new Date(current));
      }

      current.setDate(current.getDate() + 1);
    }

    return dates;
  }

    // Initialize variables for date tracking
    let startDate = null;
    let isSelecting = false;
  
    // Set current month and year
    const today = new Date();
    let currentMonth = today.getMonth();
    let currentYear = today.getFullYear();
  
    // Function to fetch holidays for a given year and month
    async function fetchHolidays(year, month) {
      try {
        const response = await fetch(`/get-all-holidays/?year=${year}&month=${month}`);
        const data = await response.json();
        return { 
          employeeHolidays: data.employee_holidays,
          publicHolidays: data.public_holidays,
        };
      } catch (error) {
        console.error("Error fetching holidays:", error);
        return {
          employeeHolidays: [],
          publicHolidays: [],
        };
      }
    }
  
    // Function to create the calendar with holidays
    async function createCalendarWithHolidays(date) {
      const monthDays = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
      const firstDay = new Date(date.getFullYear(), date.getMonth(), 1).getDay();
      if (monthYear) {
        monthYear.textContent = `${date.toLocaleString("default", { month: "long" })} ${date.getFullYear()}`;
      }
  
      try {
        const holidays = await fetchHolidays(date.getFullYear(), date.getMonth() + 1);
        const employeeHolidays = holidays.employeeHolidays;
        const publicHolidays = holidays.publicHolidays;
  
        // Create calendar rows and cells
        const fragment = document.createDocumentFragment();
        for (let i = 0; i < 6; i++) {
          const row = document.createElement("tr");
          for (let j = 0; j < 7; j++) {
            const cell = document.createElement("td");
  
            const day = i * 7 + j - firstDay + 1;
            if (day > 0 && day <= monthDays) {
              cell.dataset.date = new Date(date.getFullYear(), date.getMonth(), day).toISOString();
  
              // Add inner div for displaying names
              const nameDiv = document.createElement("div");
              nameDiv.className = "name-container";
              cell.appendChild(nameDiv);
  
              // Add day number element
              const dayNumber = document.createElement("div");
              dayNumber.className = "day-number";
              dayNumber.textContent = day;
              cell.appendChild(dayNumber);
  
              dayNumber.textContent = day;
  
              // Check if the date is an employee holiday
              const employeeHolidaysForDay = employeeHolidays.filter(eh => {
                const ehStartDate = new Date(eh.start_date);
                ehStartDate.setHours(0, 0, 0, 0);
                const ehEndDate = new Date(eh.end_date);
                ehEndDate.setHours(0, 0, 0, 0);
                const cellDate = new Date(date.getFullYear(), date.getMonth(), day);
                cellDate.setHours(0, 0, 0, 0);
                return cellDate >= ehStartDate && cellDate <= ehEndDate;
              });
  
              // Check if the date is a public holiday
              const publicHoliday = publicHolidays.find(ph => {
                const phDate = new Date(ph.date);
                phDate.setHours(0, 0, 0, 0);
                const cellDate = new Date(date.getFullYear(), date.getMonth(), day);
                cellDate.setHours(0, 0, 0, 0);
                return cellDate.getTime() === phDate.getTime();
              });
  
              if (publicHoliday) {
                cell.classList.add("public-holiday");
                nameDiv.textContent += ` (${publicHoliday.name})`;
              }
  
              // Check if the date is an employee holiday
              // Only show an employee's off day if the day is not a public holiday
              if (!publicHoliday) {
                employeeHolidaysForDay.forEach((employeeHoliday, index) => {
                  const holidayDiv = document.createElement("div");
                  employeeHoliday.is_special = !!employeeHoliday.is_special; 
              
                  // Choose the CSS class based on whether the holiday is special
                  if (employeeHoliday.is_special) {
                      holidayDiv.className = "employee-special-holiday";
                  } else {
                      holidayDiv.className = "employee-holiday";
                  }
              
                  let holidayText = ` ${employeeHoliday.employee_name}`;
              
                  // Add "(pending)" next to the name if the holiday status is pending
                  if (employeeHoliday.status === 'pending') {
                      holidayText += ' (pending)';
                  }
              
                  holidayDiv.textContent = holidayText;
              
                  // Append the div to `nameDiv` instead of `cell`
                  nameDiv.appendChild(holidayDiv);
              
                  // If you want to add space between multiple holidays
                  holidayDiv.style.marginTop = `${index * 20}px`;  // Adjust the '20' to whatever spacing you want
              });
              }
  
              if (startDate) {
                const cellDate = new Date(cell.dataset.date);
                if (isSelecting && cellDate >= startDate) {
                  cell.classList.add("marked");
                } else if (!isSelecting && cellDate > startDate && cellDate < new Date()) {
                  cell.classList.add("marked");
                }
              }
  
            } else {
              cell.classList.add("empty");
            }
  
            // Add event listeners for mouse enter and click events
            cell.addEventListener("mouseenter", () => {
              if (isSelecting) {
                const endDate = new Date(cell.dataset.date);
                markDatesInRange(startDate, endDate);
              }
            });
  
            cell.addEventListener("click", () => {
              const clickedDate = new Date(cell.dataset.date);

              if (!selectedRange.start || (selectedRange.start && selectedRange.end)) {
                // Start a new selection
                selectedRange = { start: clickedDate, end: null };
                startDate = clickedDate;
                isSelecting = true;
                cell.classList.add("selected");
              } else {
                // Finish the selection
                selectedRange.end = clickedDate;
                startDate = null;
                isSelecting = false;

                // Ensure start is before end
                if (selectedRange.start > selectedRange.end) {
                  const temp = selectedRange.start;
                  selectedRange.start = selectedRange.end;
                  selectedRange.end = temp;
                }

                markDatesInRange(selectedRange.start, selectedRange.end);
              }

              cell.dataset.utcDate = clickedDate.toISOString();
            });

            row.appendChild(cell);
          }
          fragment.appendChild(row);
        }
  
        // Clear existing calendar and append new calendar
        if (calendarBody){
          calendarBody.innerHTML = "";
          calendarBody.appendChild(fragment);
        }
        if (selectedRange.start && selectedRange.end) {
          markDatesInRange(selectedRange.start, selectedRange.end);
        }
  
      } catch (error) {
        console.error("Error creating calendar with holidays:", error);
      }
    }
  
  
    // Add event listeners for previous and next month buttons
    if (prevMonthBtn) {
      prevMonthBtn.addEventListener("click", async () => {
        currentMonth--;
        if (currentMonth < 0) {
          currentYear--;
          currentMonth = 11;
        }
        createCalendarWithHolidays(new Date(currentYear, currentMonth, 1));
      });
    }
  
    if (nextMonthBtn) {
      nextMonthBtn.addEventListener("click", async () => {
        currentMonth++;
        if (currentMonth > 11) {
          currentYear++;
          currentMonth = 0;
        }
        createCalendarWithHolidays(new Date(currentYear, currentMonth, 1));
      });
    }
  
    // Function to mark dates in a given range
    function markDatesInRange(start, end) {
      if (end < start) return;

      const cells = calendarBody.querySelectorAll("td");

      // Step 1: Clear all existing highlights
      cells.forEach(cell => {
        cell.classList.remove("marked");
        cell.classList.remove("selected");
      });

      // Step 2: Add .marked and .selected classes to visible cells
      cells.forEach(cell => {
        const cellDate = new Date(cell.dataset.date);
        if (cellDate.getTime() === start.getTime() || cellDate.getTime() === end.getTime()) {
          cell.classList.add("selected");
        } else if (cellDate > start && cellDate < end) {
          cell.classList.add("marked");
        }
      });

      // ✅ Step 3: Count ALL business days in the full range using helper function
      const fullRangeCount = getAllBusinessDatesInRange(start, end).length;

      // Step 4: Update UI counter
      dateCounter.textContent = `Business Days Selected: ${fullRangeCount}`;

      // Debug log (optional)
      console.log(`Full range: ${start.toDateString()} - ${end.toDateString()}. Business days = ${fullRangeCount}`);
    }


  
    // Add event listener for Clear Selection button
    if (clearSelectionBtn){
      clearSelectionBtn.addEventListener("click", () => {
        startDate = null;
        isSelecting = false;
        selectedRange = { start: null, end: null };

        markDatesInRange(new Date(0), new Date(0));
        dateCounter.textContent = "";
      });
    }
    // Call createCalendarWithHolidays when the page loads
    createCalendarWithHolidays(new Date(currentYear, currentMonth, 1));
  
  
    // function to show error notifications like that holidays api didn't work
    function showErrorNotification(message) {
      console.log("Showing error notification");
      const container = document.getElementById("notificationContainer");
  
      const notification = document.createElement("div");
      notification.className = "error-notification";
      notification.textContent = message;
  
      container.appendChild(notification);
  
      setTimeout(() => {
        container.removeChild(notification);
      }, 5000);
    }
      
    function submitRequest(startDate, endDate) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const utcStartDate = new Date(Date.UTC(startDate.getFullYear(), startDate.getMonth(), startDate.getDate()));
        const utcEndDate = new Date(Date.UTC(endDate.getFullYear(), endDate.getMonth(), endDate.getDate()));

        const isSpecialCheckbox = document.getElementById("is_special");
        const isSpecial = isSpecialCheckbox.checked;

        let specialTypeId = null;
        if (isSpecial) {
            const specialTypeSelect = document.getElementById("special_type");
            specialTypeId = specialTypeSelect.value;
        }
        const year = startDate.getFullYear();

        // Show loading spinner
        document.getElementById("loadingOverlay").style.display = "flex";

        fetch('/submit-holiday-request/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({
                start_date: utcStartDate.toISOString().slice(0, 10),
                end_date: utcEndDate.toISOString().slice(0, 10),
                is_special: isSpecial,
                special_type_id: specialTypeId,
                year: year
            }),
        })
        .then((response) => response.json())
        .then((data) => {
            // Hide loading spinner
            document.getElementById("loadingOverlay").style.display = "none";

            if (data.status === 'success') {
                console.log('Holiday request submitted successfully');
                $('#confirmationModal').modal('hide');
                location.reload();
            } else {
                console.error('Error submitting the holiday request:', data.message);
                $('#errorModal').modal('show');
            }
        })
        .catch((error) => {
            console.error('Unexpected error:', error);
            document.getElementById("loadingOverlay").style.display = "none";
            $('#errorModal').modal('show');
        });
    }


  function hasRangeOverlap(startDate, endDate, pastHolidays) {
    const rangeStart = new Date(startDate);
    const rangeEnd = new Date(endDate);

    rangeStart.setHours(0, 0, 0, 0);
    rangeEnd.setHours(0, 0, 0, 0);

    for (const past of pastHolidays) {
      if (past.is_deleted) continue;

      const pastStart = new Date(past.start_date);
      const pastEnd = new Date(past.end_date);

      pastStart.setHours(0, 0, 0, 0);
      pastEnd.setHours(0, 0, 0, 0);

      if (rangeStart <= pastEnd && rangeEnd >= pastStart) {
        return true;
      }
    }

    return false;
  }
  const submitHolidayRequestBtn = document.getElementById("submitHolidayRequest");
  if (submitHolidayRequestBtn) {
    submitHolidayRequestBtn.addEventListener("click", function () {
      let pastHolidays = [];

      fetch('/get-user-existing-holidays/')
        .then(response => response.json())
        .then(data => {
          pastHolidays = data.past_holidays;

          fetch('/get-available-holidays/')
            .then(response => response.json())
            .then(data => {
              const availableHolidays = data.available_holidays;

              // ✅ Use selectedRange instead of marked DOM cells
              const startDate = selectedRange.start;
              const endDate = selectedRange.end;

              if (!startDate || !endDate) {
                $('#errorModal').modal('show');
                return;
              }

              // ✅ Generate all business dates between start and end
              const businessDays = getAllBusinessDatesInRange(startDate, endDate);
              const totalHolidays = businessDays.length;

              if (hasRangeOverlap(startDate, endDate, pastHolidays)) {
                $('#pastDatesErrorModal').modal('show');
              } else if (totalHolidays > availableHolidays) {
                $('#noHolidaysModal').modal('show');
              } else if (totalHolidays === 0) {
                $('#errorModal').modal('show');
              } else {
                const isSpecialCheckbox = document.getElementById("is_special");
                const isSpecial = isSpecialCheckbox.checked;

                if (isSpecial) {
                  const specialTypeSelect = document.getElementById("special_type");
                  const specialTypeId = specialTypeSelect.value;
                  const currentYear = new Date().getFullYear();

                  fetch(`/get-special-holiday-usage/?special_type_id=${specialTypeId}&year=${currentYear}`)
                    .then(response => response.json())
                    .then(data => {
                      const maxDays = data.max_days;
                      const usedDays = data.used_days;
                      const totalDaysTaken = totalHolidays;

                      if (totalDaysTaken + usedDays > maxDays) {
                        $('#exceededSpecialHolidayModal').modal('show');
                      } else {
                        document.getElementById("selectedDateRange").innerText = `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`;
                        document.getElementById("totalHolidays").innerText = totalHolidays;
                        $('#confirmationModal').modal('show');
                      }
                    });
                } else {
                  document.getElementById("selectedDateRange").innerText = `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`;
                  document.getElementById("totalHolidays").innerText = totalHolidays;
                  $('#confirmationModal').modal('show');
                }
              }
            });
        });
    });
  }

  
  const confirmRequestBtn = document.getElementById("confirmRequest");
  if (confirmRequestBtn) {
    confirmRequestBtn.addEventListener("click", function () {
      if (selectedRange.start && selectedRange.end) {
        submitRequest(selectedRange.start, selectedRange.end);
      } else {
        $('#errorModal').modal('show');
      }
    });
  }

  
  });
  
  
  // Add an event listener for the "Toggle Theme" button
  document.getElementById("toggleTheme").addEventListener("click", function () {
    const body = document.body;
    const themeIcon = document.getElementById("themeIcon");
    body.classList.toggle("dark-theme");
  
    if (body.classList.contains("dark-theme")) {
      themeIcon.classList.remove("fas", "fa-moon");
      themeIcon.classList.add("fas", "fa-sun");
    } else {
      themeIcon.classList.remove("fas", "fa-sun");
      themeIcon.classList.add("fas", "fa-moon");
    }
  });
  loadTheme();
  
  // Add an event listener for the "Toggle Theme" button to store the theme in localStorage
  document.getElementById('toggleTheme').addEventListener('click', () => {
    let theme = localStorage.getItem('theme');
    if (theme === 'dark') {
      localStorage.setItem('theme', 'light');
    } else {
      localStorage.setItem('theme', 'dark');
    }
  });
  
  // Add event listener to tabs
  const tabs = document.querySelectorAll('.nav-link');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const tabHref = tab.getAttribute('href');
      localStorage.setItem('activeTab', tabHref);
    });
  });
  
  // Load the active tab
  function loadActiveTab() {
    const activeTab = localStorage.getItem('activeTab');
    if (activeTab) {
      $(`[href="${activeTab}"]`).tab('show');
    } else {
      // If there's no active tab in localStorage, show the first one
      tabs[0].click();
    }
  }
  
  // Call the function to load the active tab
  loadActiveTab();
  
  // Load theme
  function loadTheme() {
    let theme = localStorage.getItem('theme');
    if (theme === 'dark') {
      document.body.classList.add('dark-theme');
      document.getElementById('themeIcon').classList.replace('fa-moon', 'fa-sun');
    } else {
      document.body.classList.remove('dark-theme');
      document.getElementById('themeIcon').classList.replace('fa-sun', 'fa-moon');
    }
  }
  
  loadTheme();
  