angular.module('stiny')

.config(['$routeProvider', 'CONST', ($routeProvider, CONST) ->
  $routeProvider.when('/', {
    controller: 'HomeCtrl'
    templateUrl: "#{ CONST.URL_PREFIX }/app/home.html"
    resolve:
      partyReq: ['$http', ($http) ->
        return $http.get('/api/home/party')
      ]
  })
])

.controller('HomeCtrl', ['$scope', '$http', '$timeout', 'partyReq', 'stToast',
($scope, $http, $timeout, partyReq, stToast) ->
  $scope.partyMode = partyReq.data.party

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

  $scope.toggleParty = ->
    $scope.partyDisabled = true
    $http.post("/api/home/party_toggle").success((data, status, headers, config) ->
      $scope.partyMode = data.party
      if data.party
        stToast.toast("Party time!")
      else
        stToast.toast("You're killing the mood, man")
      $scope.partyDisabled = false
    ).error((data, status, headers, config) ->
      stToast.toast("Could not toggle party mode")
      $scope.partyDisabled = false
    )

])
