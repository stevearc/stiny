angular.module('stiny')

.directive('stLogin', ['CONST', (CONST) ->
  templateUrl: "#{ CONST.URL_PREFIX }/app/login.html"
  restrict: 'A'
  replace: true
  controller: 'LoginCtrl'
])

.controller('LoginCtrl', ['$scope', '$location', '$http',
($scope, $location, $http) ->

  $scope.login = (event, form) ->
    $scope.error = null
    data = {
      username: form.username.$modelValue
      password: form.password.$modelValue
    }

    $scope.processing = true
    $http.post("/api/login", data).success((data, status, headers, config) ->
      if data.error
        $scope.processing = false
        $scope.error = data.error
      else
        location.reload()
    ).error((data, status, headers, config) ->
      $scope.processing = false
      $scope.error = "Server error"
    )

])
