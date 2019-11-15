window.onload=function(){
      
    $(function() {
    
      var menu = $(".us-autocomplete-pro-menu");
      var input = $("#us-autocomplete-pro-address-input");
    
      function getSuggestions(search, selected) {
        $.ajax({
          url: "https://us-autocomplete.api.smartystreets.com/suggest?",
          data: {
            "auth-id": "29571869397081451",
            "prefix": search,
            "selected": (selected ? selected : "")
          },
          dataType: "jsonp",
          success: function(data) {
            if (data.suggestions) {
              buildMenu(data.suggestions);
            } else {
              noSuggestions();
            }
          },
          error: function(error) {
            return error;
          }
        });
      }
    
      function getSingleAddressData(address) {
        $.ajax({
          url: "https://us-street.api.smartystreets.com/street-address?",
          data: {
            "auth-id": "29571869397081451",
            "street": address[0],
            "city": address[1],
            "state": address[2]
          },
          dataType: "jsonp",
          success: function(data) {
            $("#zip").val(data[0].components.zipcode);
            $("#data-lat").html(data[0].metadata.latitude);
            $("#data-lon").html(data[0].metadata.longitude);
            $("#data-county").html(data[0].metadata.county_name);
            $("#data-time-zone").html(data[0].metadata.time_zone);
          },
          error: function(error) {
            return error;
          }
        });
      }
    
      function clearAddressData() {
        $("#city").val("");
        $("#state").val("");
        $("#zip").val("");
        $("#data-lat").empty();
        $("#data-lon").empty();
        $("#data-county").empty();
        $("#data-time-zone").empty();
      }
    
      function noSuggestions() {
        var menu = $(".us-autocomplete-pro-menu");
        menu.empty();
        menu.append("<li class='ui-state-disabled'><div>No Suggestions Found</div></li>");
        menu.menu("refresh");
      }
    
      function buildAddress(suggestion) {
        var whiteSpace = "";
        if (suggestion.secondary || suggestion.entries > 1) {
          if (suggestion.entries > 1) {
            suggestion.secondary += " (" + suggestion.entries + " more entries)";
          }
          whiteSpace = " ";
        }
        var address = suggestion.street_line + whiteSpace + suggestion.secondary + " " + suggestion.city + ", " + suggestion.state;
        var inputAddress = $("#us-autocomplete-pro-address-input").val();
        for (var i = 0; i < address.length; i++) {
          var theLettersMatch = typeof inputAddress[i] == "undefined" || address[i].toLowerCase() !== inputAddress[i].toLowerCase();
          if (theLettersMatch) {
            address = [address.slice(0, i), "<b>", address.slice(i)].join("");
            break;
          }
        }
        return address;
      }
    
      function buildMenu(suggestions) {
        var menu = $(".us-autocomplete-pro-menu");
        menu.empty();
        suggestions.map(function(suggestion) {
          var caret = (suggestion.entries > 1 ? "<span class=\"ui-menu-icon ui-icon ui-icon-caret-1-e\"></span>" : "");
          menu.append("<li><div data-address='" +
            suggestion.street_line + (suggestion.secondary ? " " + suggestion.secondary : "") + ";" +
            suggestion.city + ";" +
            suggestion.state + "'>" +
            caret +
            buildAddress(suggestion) + "</b></div></li>");
        });
        menu.menu("refresh");
      }
    
      $(".us-autocomplete-pro-menu").menu({
        select: function(event, ui) {
          var text = ui.item[0].innerText;
          var address = ui.item[0].childNodes[0].dataset.address.split(";");
          var searchForMoreEntriesText = new RegExp(/(?:\ more\ entries\))/);
          input.val(address[0]);
          $("#city").val(address[1]);
          $("#state").val(address[2]);
    
          if (text.search(searchForMoreEntriesText) == "-1") {
            $(".us-autocomplete-pro-menu").hide();
            getSingleAddressData(address);
          } else {
            $("#us-autocomplete-pro-address-input").val(address[0] + " ");
            var selected = text.replace(" more entries", "");
            selected = selected.replace(",", "");
            getSuggestions(address[0], selected);
          }
        }
      });
    
      $("#us-autocomplete-pro-address-input").keyup(function(event) {
        if (input.val().length > 0 || input.val() === "") clearAddressData();
        if (event.key === "ArrowDown") {
          menu.focus();
          menu.menu("focus", null, menu.menu().find(".ui-menu-item"));
        } else {
          var textInput = input.val();
          if (textInput) {
            menu.show();
            getSuggestions(textInput);
          } else {
            menu.hide();
          }
        }
      });
    
      $(".us-autocomplete-pro-menu").css("width", ($("#us-autocomplete-pro-address-input").width() + 24) + "px")
    
    });
    
    
        }
    
      //]]>