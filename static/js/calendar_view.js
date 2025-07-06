document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var businessHoursStart = calendarEl.dataset.businessHoursStart;
    var businessHoursEnd = calendarEl.dataset.businessHoursEnd;
    var tagify = new Tagify(document.getElementById('eventAttendees'), {
        tagTextProp: 'name', // Use 'name' for display, 'value' (email) for data
        placeholder: "ایمیل‌ها را اضافه کرده و Enter را فشار دهید...",
        maxTags: 10, // Example: Limit to 10 attendees
        dropdown: {
            maxItems: 20,           // <- mixumum allowed rendered suggestions
            classname: "tagify__inline__suggestions", // <- custom classname for this specific dropdown
            enabled: 0,             // <- show suggestions on focus
            closeOnSelect: false    // <- do not hide the suggestions dropdown once an item has been selected
        }
    });

    var controller; // To abort previous fetch requests

    function onInput(e) {
        var value = e.detail.value;
        tagify.whitelist = null; // Clear current whitelist

        // Abort any previous request
        if (controller) {
            controller.abort();
        }
        controller = new AbortController();

        // Show loading animation and hide dropdown
        tagify.loading(true).dropdown.hide();

        if (value.length < 2) {
            tagify.loading(false);
            return;
        }

        fetch(`/api/users/search/?q=${value}`, { signal: controller.signal })
            .then(res => res.json())
            .then(function(newWhitelist) {
                tagify.whitelist = newWhitelist; // Update whitelist with server response
                tagify.loading(false).dropdown.show(value); // Show the suggestions
            })
            .catch(err => {
                if (err.name !== 'AbortError') {
                    console.error(err);
                    tagify.loading(false);
                }
            });
    }

    tagify.on('input', onInput);
    var createEventModalEl = document.getElementById('createEventModal');
    var createEventModal = new bootstrap.Modal(createEventModalEl);
    var eventTitleInput = document.getElementById('eventTitle');
    var saveEventButton = document.getElementById('saveEventButton');
    var currentSelectionInfo = null; // Global variable to store selection info

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek', // Changed to timeGridWeek for better time selection
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        locale: 'fa', // Translate to Persian
        firstDay: 6, // Week starts on Saturday (Shanbe)
        weekends: true, // Explicitly enable weekends
        businessHours: {
            daysOfWeek: [ 0, 1, 2, 3, 6 ], // Sunday - Wednesday, Saturday (excluding Thursday and Friday)
            startTime: businessHoursStart, // 8 AM
            endTime: businessHoursEnd // 6 PM
        },
        slotMinTime: businessHoursStart, // Start calendar at 8 AM
        slotMaxTime: businessHoursEnd, // End calendar at 6 PM
        selectable: true, // Enable selection
        selectMirror: true, // Show a mirror image of the selected area
        editable: true, // Enable dragging and resizing
// START OF CHANGES - Step 2
    select: function(info) {
        // Prevent creating events in month view
        if (info.view.type === 'dayGridMonth') {
            alert("لطفاً برای ایجاد رزرو جدید، یک بازه زمانی را در نمای هفته یا روز انتخاب کنید.");
            calendar.unselect(); // Unselect the date range
            return;
        }
        
        // Store the selection info
        currentSelectionInfo = info;
        
        // Clear all modal fields
        eventTitleInput.value = '';
        document.getElementById('eventGeneralDescription').value = '';
        document.getElementById('eventITSupport').checked = false;
        
        // Get the new room dropdown from the modal
        var eventRoomSelect = document.getElementById('eventRoom');
        
        // Get the currently selected room from the main page filter
        var mainFilterRoomId = document.getElementById('room-filter').value;
        
        // Pre-select the room in the modal if it's selected in the main filter
        if (mainFilterRoomId) {
            eventRoomSelect.value = mainFilterRoomId;
        } else {
            // Otherwise, reset to the default "Select a room..." option
            eventRoomSelect.value = "";
        }
        
        // Show the Bootstrap modal
        createEventModal.show();
    },
    // END OF CHANGES - Step 2
        eventDidMount: function(info) {
            // A better way to pass room_id and other data
            if (info.event.extendedProps) {
                info.event.extendedProps.room_id = info.event.extendedProps.room_id || null;
            }
        },

        eventSources: [
            // Source 1: Our existing reservations API
            {
                id: 'reservations', // Add an ID to reference this source
                url: calendarEl.dataset.eventsUrl, // Static URL
                failure: function() {
                    alert('خطایی در دریافت رزروها رخ داد!');
                },
            },
            // Source 2: Iranian Holidays from Google Calendar
            {
                googleCalendarId: 'fa.ir#holiday@group.v.calendar.google.com',
                className: 'gcal-event', // for custom styling
                display: 'background' // Makes holidays look like background events
            }
        ],
        // googleCalendarApiKey: 'YOUR_GOOGLE_CALENDAR_API_KEY', // Placeholder for API key
        // Makes events clickable
        eventClick: function(info) {
            info.jsEvent.preventDefault(); // Always prevent default navigation

            var props = info.event.extendedProps;
            // In a real app, you would get the current user's username from the template.
            // For this example, let's assume it's available via a template variable.
            var currentUser = "{{ request.user.username }}";
            
            // Allow editing only if the user is the organizer
            if (props.organizer_username !== currentUser) {
                alert("شما فقط می‌توانید رزروهای خود را ویرایش کنید.");
                return;
            }

            // --- Pre-fill and open the modal for editing ---
            document.getElementById('createEventModalLabel').innerText = 'ویرایش جلسه'; // Change modal title
            document.getElementById('eventPk').value = props.pk; // Set the hidden event ID
            document.getElementById('eventTitle').value = info.event.title;
            // Populate Tagify with attendees
            if (props.attendee_list) {
                tagify.removeAllTags(); // Clear existing tags
                tagify.addTags(props.attendee_list); // Add new tags
            } else {
                tagify.removeAllTags(); // Ensure it's empty if no attendees
            }
            var itSupportCheckbox = document.getElementById('eventITSupport');
            var itSupportDetailsContainer = document.getElementById('itSupportDetailsContainer');
            var itDescriptionTextarea = document.getElementById('eventITDescription');
            var generalDescriptionTextarea = document.getElementById('eventGeneralDescription');

            var isITSupportChecked = (props.it_support === 'Yes');
            itSupportCheckbox.checked = isITSupportChecked;

            // Split the description back into general and IT parts
            var fullDescription = props.description || '';
            var itMarker = "\n--- IT Support Requirements ---\n";
            var itDescIndex = fullDescription.indexOf(itMarker);

            if (isITSupportChecked && itDescIndex !== -1) {
                generalDescriptionTextarea.value = fullDescription.substring(0, itDescIndex).trim();
                itDescriptionTextarea.value = fullDescription.substring(itDescIndex + itMarker.length).trim();
            } else {
                generalDescriptionTextarea.value = fullDescription;
                itDescriptionTextarea.value = '';
            }
            
            itSupportDetailsContainer.style.display = isITSupportChecked ? 'block' : 'none';

            // Find the room_id by its name (a bit fragile, but works for this case)
            // A better approach would be to pass room_id in extendedProps as well.
            var roomSelect = document.getElementById('eventRoom');
            for(var i=0; i < roomSelect.options.length; i++) {
                if(roomSelect.options[i].text === props.room_name) {
                    roomSelect.value = roomSelect.options[i].value;
                    break;
                }
            }

            // We need to store the start/end times for the save function
            currentSelectionInfo = {
                startStr: info.event.startStr,
                endStr: info.event.endStr
            };

            document.getElementById('deleteEventButton').style.display = 'inline-block'; // Show delete button
            createEventModal.show();
        },
        eventDrop: function(info) {
            var event = info.event;
            var newStart = event.start.toISOString();
            var newEnd = event.end ? event.end.toISOString() : null; // End might be null for all-day events

            // Get the CSRF token from the modal's form
            var csrfToken = createEventModalEl.querySelector('input[name="csrfmiddlewaretoken"]').value;
            var urlTemplate = `/api/reservations/${event.extendedProps.pk}/drag_update/`; 
var url = urlTemplate.replace('9999', event.extendedProps.pk);

            fetch(url, {
                method: 'PATCH', // Using PATCH to partially update the event
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    start: newStart,
                    end: newEnd
                })
            })
            .then(response => {
                if (!response.ok) {
                    // If the server responds with an error, revert the event's position
                    info.revert();
                    return response.json().then(data => {
                        alert('خطا در به‌روزرسانی رویداد: ' + (data.error || 'خطای ناشناخته'));
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data) {
                    console.log('Event updated successfully:', data);
                    calendar.refetchEvents(); // Refetch to ensure data is fresh
                }
            })
            .catch(error => {
                console.error('Error:', error);
                info.revert();
                alert('خطای شبکه هنگام به‌روزرسانی رویداد رخ داد.');
            });
        },

        eventMouseEnter: function(info) {
            // Prepare the content for the popover
            var props = info.event.extendedProps;
            var popoverContent = `
                <ul class="list-unstyled mb-0">
                    <li><strong class="me-2">اتاق:</strong>${props.room_name}</li>
                    <li><strong class="me-2">برگزارکننده:</strong>${props.organizer_username}</li>
                    <li><strong class="me-2">پشتیبانی IT:</strong>${props.it_support}</li>
                `;
            if (props.attendee_list && props.attendee_list.length > 0) {
                var attendeeNames = props.attendee_list.map(att => att.name).join(', ');
                popoverContent += `<li><strong class="me-2">شرکت‌کنندگان:</strong>${attendeeNames}</li>`;
            }
            if (props.description) {
                popoverContent += `<li><strong class="me-2">توضیحات:</strong>${props.description}</li>`;
            }
            popoverContent += `</ul>`;

            // Initialize and show the Bootstrap Popover
            var popover = bootstrap.Popover.getOrCreateInstance(info.el, {
                title: info.event.title,
                content: popoverContent,
                placement: 'top',
                trigger: 'manual', // We will show/hide it manually
                html: true,
                sanitize: false, // We are creating the HTML, so it's safe
                container: 'body' // Important to prevent the popover from being trapped inside the calendar's scroll container
            });
            popover.show();
        },

        eventMouseLeave: function(info) {
            // Dispose of the popover when the mouse leaves
            var popover = bootstrap.Popover.getInstance(info.el);
            if (popover) {
                popover.dispose();
            }
        },

        expandRows: true
    });
    calendar.render();

    // Event listener for the Save button, defined only once
// START OF CHANGES - Step 3
    saveEventButton.addEventListener('click', function() {
        if (!currentSelectionInfo) {
            alert('بازه زمانی انتخاب نشده است.');
            return;
        }

        var eventPk = document.getElementById('eventPk').value;
        var isUpdate = !!eventPk; // Check if we are in "update" mode

        var title = document.getElementById('eventTitle').value;
        var roomId = document.getElementById('eventRoom').value;

        if (!title || !roomId) {
            alert('عنوان و اتاق فیلدهای الزامی هستند.');
            return;
        }

        var generalDesc = document.getElementById('eventGeneralDescription').value.trim();
        var itSupportNeeded = document.getElementById('eventITSupport').checked;
        var itDesc = document.getElementById('eventITDescription').value.trim();
        
        var finalDescription = generalDesc;
        if (itSupportNeeded && itDesc) {
            // Combine descriptions with a clear marker
            finalDescription += "\n\n--- IT Support Requirements ---\n" + itDesc;
        } else if (itSupportNeeded && !itDesc) {
            // If box is checked but field is empty, just note that support is needed.
            finalDescription += "\n\n--- IT Support Required ---";
        }

        var attendeeEmails = tagify.value.map(tag => tag.value); // Get attendee emails from Tagify
        var postData = {
            title: title,
            description: finalDescription,
            it_support_needed: itSupportNeeded,
            room_id: parseInt(roomId),
            start: currentSelectionInfo.startStr,
            end: currentSelectionInfo.endStr,
            attendees: attendeeEmails, // Add attendee emails to postData
        };

        var url = isUpdate ? `/api/reservations/${eventPk}/update/` : `/api/reservations/quick_create/`;
        var method = isUpdate ? 'PUT' : 'POST';
        var csrfToken = createEventModalEl.querySelector('input[name="csrfmiddlewaretoken"]').value;

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(postData)
        })
        .then(response => response.json().then(data => ({status: response.status, body: data})))
        .then(result => {
            if (result.status >= 200 && result.status < 300) {
                createEventModal.hide();
                calendar.refetchEvents();
            } else {
                alert('خطا: ' + (result.body.error || 'خطای ناشناخته سرور'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('خطای شبکه رخ داد.');
        });
    });
    document.getElementById('deleteEventButton').addEventListener('click', function() {
        var eventPk = document.getElementById('eventPk').value;
        if (!eventPk) {
            alert('نمی‌توان رویدادی را بدون شناسه حذف کرد.');
            return;
        }

        if (confirm('آیا از حذف دائمی این رزرو اطمینان دارید؟')) {
            var url = `/api/reservations/${eventPk}/delete/`;
            var csrfToken = createEventModalEl.querySelector('input[name="csrfmiddlewaretoken"]').value;

            fetch(url, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => {
                if (response.ok) { // Status 200-299
                    return response.json();
                } else {
                    // Try to get error message from backend
                    return response.json().then(data => { throw new Error(data.error || 'حذف ناموفق بود.'); });
                }
            })
            .then(result => {
                console.log(result.message);
                createEventModal.hide();
                calendar.refetchEvents();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('خطا در حذف رزرو: ' + error.message);
            });
        }
    });
    // END OF CHANGES - Step 3

    // Unselect on modal close and reset state
    document.getElementById('createEventModal').addEventListener('hidden.bs.modal', function () {
        document.getElementById('deleteEventButton').style.display = 'none'; // Hide delete button on close
        document.getElementById('createEventModalLabel').innerText = 'جلسه جدید';
        // Reset the form to be ready for a "create" action next time
        document.getElementById('createEventModalLabel').innerText = 'جلسه جدید';
        document.getElementById('eventPk').value = ''; // Clear the hidden ID
        
        // --- Reset IT Support field and hide its description ---
        var itSupportCheckbox = document.getElementById('eventITSupport');
        itSupportCheckbox.checked = false;
        document.getElementById('itSupportDetailsContainer').style.display = 'none';
        document.getElementById('eventITDescription').value = '';
        // --- End of Reset ---

        document.getElementById('eventTitle').value = '';
        document.getElementById('eventGeneralDescription').value = '';
        document.getElementById('eventRoom').value = '';
        tagify.removeAllTags(); // Clear Tagify input on modal close
        
        calendar.unselect();
        currentSelectionInfo = null; // Reset state
    });

    document.getElementById('room-filter').addEventListener('change', function() {
        var roomId = this.value; // Get the selected room ID

        // Remove the existing reservations event source
        var existingSource = calendar.getEventSourceById('reservations');
        if (existingSource) {
            existingSource.remove();
        }

        // Construct the new URL for reservations
        var newApiUrl = calendarEl.dataset.eventsUrl;
        if (roomId) {
            newApiUrl += '?room_id=' + roomId;
        }

        // Add the new event source
        calendar.addEventSource({
            id: 'reservations',
            url: newApiUrl,
            failure: function() {
                alert('خطایی در دریافت رزروها رخ داد!');
            },
        });
    });
    
    // --- START OF CHANGES - Step 2 ---
    // Logic to show/hide the IT support description box
    var itSupportCheckbox = document.getElementById('eventITSupport');
    var itSupportDetailsContainer = document.getElementById('itSupportDetailsContainer');

    itSupportCheckbox.addEventListener('change', function() {
        itSupportDetailsContainer.style.display = this.checked ? 'block' : 'none';
        if (!this.checked) {
            document.getElementById('eventITDescription').value = ''; // Clear IT description if unchecked
        }
    });
    // --- END OF CHANGES - Step 2 ---
});