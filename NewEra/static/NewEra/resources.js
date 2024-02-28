// THIS FILE IS LINKED FROM THE FOLLOWING LOCATIONS: 
// resources.html


// -------- FILTER ACTION --------

// Uncheck all filters
function uncheckAll(event) {
    event.preventDefault()

    $("#filter-card .scroll-section input").prop("checked", false)
}

// Search through given filters 
function searchFilters() {
    event.preventDefault()

    var search = $('#filter-search')[0].value.split(' ')

    $("#filter-card .scroll-section label").each(function(){ 
        var filter = this.innerText.toUpperCase()
        var includesQuery = false

        for (i = 0; i < search.length; i++) {
            var query = search[i].toUpperCase()

            if (filter.includes(query)) {
                includesQuery = true
                break
            }
        }

        if(!includesQuery) { 
            if(!$(this).find('input').is(':checked')) {
                $(this).hide()
            }
        } else {
            $(this).show()
            // $(this).attr('state','out')
            // $(this).click(toggleItem)
        }
    })

    
}