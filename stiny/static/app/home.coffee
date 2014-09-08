angular.module('stiny')

.config(['$routeProvider', 'CONST', ($routeProvider, CONST) ->
  $routeProvider.when('/', {
    controller: 'HomeCtrl'
    templateUrl: "#{ CONST.URL_PREFIX }/app/home.html"
  })
])

.controller('HomeCtrl', ['$scope', '$http', '$timeout', 'stToast',
($scope, $http, $timeout, stToast) ->

  $scope.unlock = ->
    $scope.unlockDisabled = true
    $http.post("/api/home/unlock").success((data, status, headers, config) ->
      stToast.toast("Unlocked!")
      $timeout(->
        $scope.unlockDisabled = false
      , 5000)
    ).error((data, status, headers, config) ->
      $scope.unlockDisabled = false
      stToast.toast("Could not unlock door")
    )

  $scope.ringDoorbell = ->
    $scope.doorbellDisabled = true
    $http.post("/api/home/doorbell").success((data, status, headers, config) ->
      stToast.toast("Ding dong!")
      $timeout(->
        $scope.doorbellDisabled = false
      , 1000)
    ).error((data, status, headers, config) ->
      stToast.toast("Could not ring doorbell")
      $scope.doorbellDisabled = false
    )
])
